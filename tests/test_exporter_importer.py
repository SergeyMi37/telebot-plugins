# tests/test_exporter_importer.py
from django.test import TestCase
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django_celery_beat.models import P
from users.management.commands.export_celery_tasks import export_tasks
from users.management.commands.import_celery_tasks import import_tasks
import json

class ExporterImporterTestCase(TestCase):
    def setUp(self):
        self.crontab = CrontabSchedule.objects.create(
            minute='0',
            hour='12',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        self.task = PeriodicTask.objects.create(
            name='test_task',
            task='test_app.tasks.test_task',
            crontab=self.crontab,
            args='["arg1", "arg2"]',
            kwargs='{"kwarg1": "value1"}',
            enabled=True,
        )
    
    def test_export_task(self):
        exported = export_tasks(['test_task'])
        data = json.loads(exported)
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'test_task')
        self.assertEqual(data[0]['task'], 'test_app.tasks.test_task')
        self.assertEqual(data[0]['args'], '["arg1", "arg2"]')
        self.assertTrue(data[0]['enabled'])
        self.assertEqual(data[0]['schedule']['_type'], 'crontab')
    
    def test_import_task(self):
        # Export first
        exported = export_tasks(['test_task'])
        
        # Delete original
        PeriodicTask.objects.all().delete()
        CrontabSchedule.objects.all().delete()
        
        # Import
        result = import_tasks(exported)
        
        self.assertEqual(len(result['imported']), 1)
        self.assertEqual(result['imported'][0], 'test_task')
        
        # Verify imported task
        imported_task = PeriodicTask.objects.get(name='test_task')
        self.assertEqual(imported_task.task, 'test_app.tasks.test_task')
        self.assertTrue(imported_task.enabled)
    
    def test_dry_run_import(self):
        exported = export_tasks(['test_task'])
        result = import_tasks(exported, dry_run=True)
        
        self.assertEqual(len(result['imported']), 1)
        self.assertEqual(PeriodicTask.objects.count(), 1)  # Original still exists