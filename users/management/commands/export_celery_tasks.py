# management/commands/export_celery_tasks.py
# python manage.py export_celery_tasks --output downloads/my_tasks.json
# или для конкретных задач
# python manage.py export_celery_tasks --task-names task1 task2 --output downloads/selected_tasks.json

from django.core.management.base import BaseCommand
import json
from celery.schedules import crontab, schedule, solar
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule, SolarSchedule

def serialize_schedule(schedule_obj):
    if isinstance(schedule_obj, crontab):
        return {
            '_type': 'crontab',
            'minute': schedule_obj.minute,
            'hour': schedule_obj.hour,
            'day_of_week': schedule_obj.day_of_week,
            'day_of_month': schedule_obj.day_of_month,
            'month_of_year': schedule_obj.month_of_year,
        }
    elif isinstance(schedule_obj, schedule):
        return {
            '_type': 'interval',
            'every': schedule_obj.run_every.total_seconds(),
            'period': 'seconds',
        }
    elif isinstance(schedule_obj, solar):
        return {
            '_type': 'solar',
            'event': schedule_obj.event,
            'latitude': schedule_obj.lat,
            'longitude': schedule_obj.lon,
        }
    return None

def convert_for_json(obj):
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [convert_for_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, set):
        return list(obj)
    else:
        return str(obj)  # или другой способ сериализации

def export_tasks(task_names=None):
    tasks = PeriodicTask.objects.all()
    if task_names:
        tasks = tasks.filter(name__in=task_names)
    
    serialized_tasks = []
    for task in tasks:
        serialized = {
            'name': task.name,
            'task': task.task,
            'enabled': task.enabled,
            'description': task.description,
            'args': convert_for_json(task.args),
            'kwargs': convert_for_json(task.kwargs),
            'queue': task.queue,
            'exchange': task.exchange,
            'routing_key': task.routing_key,
            'expires': task.expires.isoformat() if task.expires else None,
            'one_off': task.one_off,
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'priority': task.priority,
            'headers': convert_for_json(task.headers),
            'last_run_at': task.last_run_at.isoformat() if task.last_run_at else None,
            'total_run_count': task.total_run_count,
        }
        
        if task.crontab:
            serialized['schedule'] = serialize_schedule(task.crontab.schedule)
        elif task.interval:
            serialized['schedule'] = serialize_schedule(task.interval.schedule)
        elif task.solar:
            serialized['schedule'] = serialize_schedule(task.solar.schedule)
        elif task.clocked:
            serialized['clocked_time'] = task.clocked.clocked_time.isoformat()
        
        serialized_tasks.append(serialized)
    
    return json.dumps(serialized_tasks, indent=2)

class Command(BaseCommand):
    help = 'Export periodic celery tasks to JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', 
            type=str,
            default='celery_tasks_export.json',
            help='Output file path'
        )
        parser.add_argument(
            '--task-names',
            type=str,
            nargs='+',
            help='Specific task names to export (space separated)'
        )

    def handle(self, *args, **options):
        output_path = options['output']
        task_names = options['task_names']
        
        result = export_tasks(task_names)
        
        with open(output_path, 'w') as f:
            f.write(result)
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully exported tasks to {output_path}'
        ))