import os
from importlib import reload
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

import fitness_tracker.settings as settings_module

from .models import Exercise, Partner, Workout


class AllowedHostsTests(TestCase):
    def test_render_hostname_is_added_to_allowed_hosts(self):
        with patch.dict(os.environ, {'RENDER_EXTERNAL_HOSTNAME': 'demo.onrender.com'}, clear=False):
            reloaded = reload(settings_module)
            self.assertIn('demo.onrender.com', reloaded.ALLOWED_HOSTS)


class DatabaseSettingsTests(TestCase):
    def test_database_url_is_used_when_present(self):
        with patch.dict(os.environ, {'DATABASE_URL': 'postgres://user:pass@localhost:5432/fitnessdb'}, clear=False):
            reloaded = reload(settings_module)
            self.assertEqual(reloaded.DATABASES['default']['ENGINE'], 'django.db.backends.postgresql')
            self.assertEqual(reloaded.DATABASES['default']['NAME'], 'fitnessdb')


class WorkoutFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='StrongPass123!')
        self.client.force_login(self.user)
        self.workout = Workout.objects.create(user=self.user, workout_name='Upper Body', workout_date='2026-01-01')

    def test_add_exercise_to_workout_detail(self):
        response = self.client.post(
            reverse('workout-detail', args=[self.workout.pk]),
            {
                'add-exercise': '1',
                'exercise_name': 'Bench Press',
                'category': 'chest',
                'display_order': 1,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Exercise.objects.filter(workout=self.workout, exercise_name='Bench Press').exists())

    def test_accept_partner_request(self):
        partner_user = get_user_model().objects.create_user(username='partner', password='StrongPass123!')
        request_obj = Partner.objects.create(user=self.user, partner_user=partner_user)
        self.client.force_login(partner_user)

        response = self.client.post(reverse('accept-partner', args=[request_obj.pk]))

        request_obj.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(request_obj.status, 'accepted')

    def test_dashboard_includes_partner_status_summary(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('partner_status', response.context)
