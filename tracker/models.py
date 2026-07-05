from django.conf import settings
from django.db import models
from django.utils import timezone


COMMON_EXERCISES = [
    ('Bench Press', 'chest'),
    ('Incline Dumbbell Press', 'chest'),
    ('Pull Ups', 'back'),
    ('Lat Pulldown', 'back'),
    ('Back Squat', 'legs'),
    ('Romanian Deadlift', 'legs'),
    ('Shoulder Press', 'shoulders'),
    ('Lateral Raises', 'shoulders'),
    ('Barbell Curl', 'arms'),
    ('Triceps Dip', 'arms'),
    ('Plank', 'core'),
    ('Mountain Climbers', 'core'),
    ('Treadmill Run', 'cardio'),
    ('Cycling', 'cardio'),
]


class Workout(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workouts')
    workout_name = models.CharField(max_length=200)
    workout_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-workout_date', '-created_at']

    def __str__(self):
        return f"{self.workout_name} ({self.user.username})"


class Exercise(models.Model):
    CATEGORY_CHOICES = [
        ('chest', 'Chest'),
        ('back', 'Back'),
        ('legs', 'Legs'),
        ('shoulders', 'Shoulders'),
        ('arms', 'Arms'),
        ('core', 'Core'),
        ('cardio', 'Cardio'),
    ]

    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='exercises')
    exercise_name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'created_at']

    def __str__(self):
        return self.exercise_name


class WorkoutSet(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='sets')
    set_number = models.PositiveIntegerField(default=1)
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    repetitions = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['set_number', 'created_at']

    def __str__(self):
        return f"Set {self.set_number} - {self.exercise.exercise_name}"


class WeightLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weight_logs')
    date = models.DateField(default=timezone.now)
    body_weight = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.body_weight}kg on {self.date}"


class Partner(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='partner_requests_sent')
    partner_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='partner_requests_received')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    accepted_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'partner_user'], name='unique_partner_request')
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.partner_user.username} ({self.status})"

    def save(self, *args, **kwargs):
        if self.status == 'accepted' and self.accepted_date is None:
            self.accepted_date = timezone.now()
        if self.status != 'accepted':
            self.accepted_date = None
        super().save(*args, **kwargs)
