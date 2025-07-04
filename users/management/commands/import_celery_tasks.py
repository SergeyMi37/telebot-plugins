# management/commands/import_celery_tasks.py
# python manage.py import_celery_tasks downloads/my_tasks.json
# для тестового запуска "сухой прогон" — это флаг, который указывает скрипту выполнить имитацию импорта задач без фактического сохранения их в базу данных
# python manage.py import_celery_tasks downloads/my_tasks.json --dry-run

from django.core.management.base import BaseCommand
#from celery_tasks_exporter.importer import import_tasks

import json
from datetime import datetime
from celery.schedules import crontab
from django.utils.timezone import make_aware
from django_celery_beat.models import (
    PeriodicTask, 
    CrontabSchedule, 
    IntervalSchedule, 
    SolarSchedule,
    ClockedSchedule
)

def deserialize_schedule(schedule_data):
    if schedule_data['_type'] == 'crontab':
        return CrontabSchedule.objects.get_or_create(
            minute=schedule_data['minute'],
            hour=schedule_data['hour'],
            day_of_week=schedule_data['day_of_week'],
            day_of_month=schedule_data['day_of_month'],
            month_of_year=schedule_data['month_of_year'],
        )[0]
    elif schedule_data['_type'] == 'interval':
        return IntervalSchedule.objects.get_or_create(
            every=int(schedule_data['every']),
            period=schedule_data['period'],
        )[0]
    elif schedule_data['_type'] == 'solar':
        return SolarSchedule.objects.get_or_create(
            event=schedule_data['event'],
            latitude=schedule_data['latitude'],
            longitude=schedule_data['longitude'],
        )[0]
    return None

def import_tasks(json_data, dry_run=False):
    data = json.loads(json_data)
    
    result = {
        'imported': [],
        'skipped': [],
        'errors': []
    }
    
    for task_data in data:
        try:
            if PeriodicTask.objects.filter(name=task_data['name']).exists():
                result['skipped'].append(task_data['name'])
                continue
            
            if dry_run:
                result['imported'].append(task_data['name'])
                continue
            
            # Handle schedule
            schedule_obj = None
            if 'schedule' in task_data and task_data['schedule']:
                schedule_obj = deserialize_schedule(task_data['schedule'])
            
            # Handle clocked time
            clocked = None
            if 'clocked_time' in task_data and task_data['clocked_time']:
                clocked_time = make_aware(datetime.fromisoformat(task_data['clocked_time']))
                clocked = ClockedSchedule.objects.create(clocked_time=clocked_time)
            
            # Create task
            task = PeriodicTask(
                name=task_data['name'],
                task=task_data['task'],
                enabled=task_data.get('enabled', True),
                description=task_data.get('description', ''),
                args=task_data.get('args', '[]'),
                kwargs=task_data.get('kwargs', '{}'),
                queue=task_data.get('queue'),
                exchange=task_data.get('exchange'),
                routing_key=task_data.get('routing_key'),
                expires=make_aware(datetime.fromisoformat(task_data['expires'])) if task_data.get('expires') else None,
                one_off=task_data.get('one_off', False),
                start_time=make_aware(datetime.fromisoformat(task_data['start_time'])) if task_data.get('start_time') else None,
                priority=task_data.get('priority'),
                headers=task_data.get('headers', '{}'),
                last_run_at=make_aware(datetime.fromisoformat(task_data['last_run_at'])) if task_data.get('last_run_at') else None,
                total_run_count=task_data.get('total_run_count', 0),
            )
            
            if schedule_obj:
                if isinstance(schedule_obj, CrontabSchedule):
                    task.crontab = schedule_obj
                elif isinstance(schedule_obj, IntervalSchedule):
                    task.interval = schedule_obj
                elif isinstance(schedule_obj, SolarSchedule):
                    task.solar = schedule_obj
            
            if clocked:
                task.clocked = clocked
            
            task.save()
            result['imported'].append(task_data['name'])
        
        except Exception as e:
            result['errors'].append({
                'task': task_data.get('name', 'unknown'),
                'error': str(e)
            })
    
    return result

class Command(BaseCommand):
    help = 'Import periodic celery tasks from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'input', 
            type=str,
            help='Input file path'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate import without saving'
        )

    def handle(self, *args, **options):
        input_path = options['input']
        dry_run = options['dry_run']
        
        with open(input_path, 'r') as f:
            data = f.read()
        
        result = import_tasks(data, dry_run=dry_run)
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                'Dry run completed. No tasks were actually imported.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Successfully imported {len(result["imported"])} tasks'
            ))
        
        if result['skipped']:
            self.stdout.write(self.style.WARNING(
                f'Skipped {len(result["skipped"])} tasks (already exist)'
            ))