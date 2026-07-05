from django.contrib import admin

from .models import Exercise, Partner, WeightLog, Workout, WorkoutSet


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('workout_name', 'user', 'workout_date', 'created_at')
    search_fields = ('workout_name', 'user__username', 'notes')


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('exercise_name', 'workout', 'category', 'display_order')
    search_fields = ('exercise_name', 'workout__workout_name')


@admin.register(WorkoutSet)
class WorkoutSetAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'set_number', 'weight', 'repetitions')
    search_fields = ('exercise__exercise_name',)


@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'body_weight')
    search_fields = ('user__username',)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'partner_user', 'status', 'accepted_date', 'created_at')
    search_fields = ('user__username', 'partner_user__username')
