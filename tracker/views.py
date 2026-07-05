from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from .forms import ExerciseForm, PartnerForm, ProfileForm, RegisterForm, WeightLogForm, WorkoutForm, WorkoutSetForm
from .models import COMMON_EXERCISES, Exercise, Partner, WeightLog, Workout, WorkoutSet


class RegisterView(CreateView):
    template_name = 'registration/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Your account has been created successfully.')
        return response


class LoginView(AuthLoginView):
    template_name = 'registration/login.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'Welcome back!')
        return super().form_valid(form)


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


@login_required
def dashboard(request):
    workouts = Workout.objects.filter(user=request.user)
    latest_weight = request.user.weight_logs.order_by('-date').first()
    last_workout = workouts.order_by('-workout_date', '-created_at').first()
    weekly_workouts = workouts.filter(workout_date__gte=timezone.now().date() - timedelta(days=7)).count()
    partner_status = Partner.objects.filter(Q(user=request.user) | Q(partner_user=request.user)).order_by('-created_at').first()

    context = {
        'latest_weight': latest_weight,
        'last_workout': last_workout,
        'workout_count': workouts.count(),
        'weekly_workouts': weekly_workouts,
        'recent_workouts': workouts.order_by('-workout_date', '-created_at')[:5],
        'partner_status': partner_status,
    }
    return render(request, 'dashboard.html', context)


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'profile.html'
    form_class = ProfileForm
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Your profile was updated successfully.')
        return super().form_valid(form)


class WorkoutListView(LoginRequiredMixin, ListView):
    model = Workout
    template_name = 'workouts/workout_list.html'
    context_object_name = 'workouts'

    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user).order_by('-workout_date', '-created_at')


class WorkoutCreateView(LoginRequiredMixin, CreateView):
    model = Workout
    form_class = WorkoutForm
    template_name = 'workouts/workout_form.html'
    success_url = reverse_lazy('workout-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Workout saved successfully.')
        return super().form_valid(form)


class WorkoutDetailView(LoginRequiredMixin, View):
    template_name = 'workouts/workout_detail.html'

    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        workout = get_object_or_404(self.get_queryset(), pk=kwargs['pk'])
        exercise_form = ExerciseForm()
        set_form = WorkoutSetForm(workout=workout)
        return render(request, self.template_name, {'workout': workout, 'exercise_form': exercise_form, 'set_form': set_form, 'common_exercises': COMMON_EXERCISES})

    def post(self, request, *args, **kwargs):
        workout = get_object_or_404(self.get_queryset(), pk=kwargs['pk'])
        if 'add-exercise' in request.POST:
            exercise_form = ExerciseForm(request.POST)
            if exercise_form.is_valid():
                exercise = exercise_form.save(commit=False)
                exercise.workout = workout
                exercise.save()
                messages.success(request, 'Exercise added to workout.')
                return redirect('workout-detail', pk=workout.pk)
            set_form = WorkoutSetForm(workout=workout)
            return render(request, self.template_name, {'workout': workout, 'exercise_form': exercise_form, 'set_form': set_form, 'common_exercises': COMMON_EXERCISES})

        set_form = WorkoutSetForm(workout=workout, data=request.POST)
        if set_form.is_valid():
            set_form.save()
            messages.success(request, 'Set added successfully.')
            return redirect('workout-detail', pk=workout.pk)
        exercise_form = ExerciseForm()
        return render(request, self.template_name, {'workout': workout, 'exercise_form': exercise_form, 'set_form': set_form, 'common_exercises': COMMON_EXERCISES})


class WorkoutUpdateView(LoginRequiredMixin, UpdateView):
    model = Workout
    form_class = WorkoutForm
    template_name = 'workouts/workout_form.html'
    success_url = reverse_lazy('workout-list')

    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Workout updated successfully.')
        return super().form_valid(form)


class WorkoutDeleteView(LoginRequiredMixin, DeleteView):
    model = Workout
    template_name = 'workouts/workout_confirm_delete.html'
    success_url = reverse_lazy('workout-list')

    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Workout deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def duplicate_workout(request, pk):
    source_workout = get_object_or_404(Workout, pk=pk, user=request.user)
    new_workout = Workout.objects.create(
        user=request.user,
        workout_name=f"{source_workout.workout_name} (Copy)",
        workout_date=timezone.now().date(),
        notes=source_workout.notes,
    )
    for exercise in source_workout.exercises.all():
        new_exercise = exercise.__class__.objects.create(
            workout=new_workout,
            exercise_name=exercise.exercise_name,
            category=exercise.category,
            display_order=exercise.display_order,
        )
        for workout_set in exercise.sets.all():
            workout_set.__class__.objects.create(
                exercise=new_exercise,
                set_number=workout_set.set_number,
                weight=workout_set.weight,
                repetitions=workout_set.repetitions,
                notes=workout_set.notes,
            )
    messages.success(request, 'Workout duplicated successfully.')
    return redirect('workout-detail', pk=new_workout.pk)


class WeightLogListView(LoginRequiredMixin, ListView):
    model = WeightLog
    template_name = 'weight/weight_list.html'
    context_object_name = 'weight_logs'

    def get_queryset(self):
        return WeightLog.objects.filter(user=self.request.user).order_by('-date', '-created_at')


class WeightLogCreateView(LoginRequiredMixin, CreateView):
    model = WeightLog
    form_class = WeightLogForm
    template_name = 'weight/weight_form.html'
    success_url = reverse_lazy('weight-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Weight log saved.')
        return super().form_valid(form)


class WeightLogUpdateView(LoginRequiredMixin, UpdateView):
    model = WeightLog
    form_class = WeightLogForm
    template_name = 'weight/weight_form.html'
    success_url = reverse_lazy('weight-list')

    def get_queryset(self):
        return WeightLog.objects.filter(user=self.request.user)


class WeightLogDeleteView(LoginRequiredMixin, DeleteView):
    model = WeightLog
    template_name = 'weight/weight_confirm_delete.html'
    success_url = reverse_lazy('weight-list')

    def get_queryset(self):
        return WeightLog.objects.filter(user=self.request.user)


class WorkoutSetUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkoutSet
    form_class = WorkoutSetForm
    template_name = 'sets/set_form.html'

    def get_queryset(self):
        return WorkoutSet.objects.filter(exercise__workout__user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['workout'] = self.object.exercise.workout
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Set updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workout-detail', args=[self.object.exercise.workout.pk])


class WorkoutSetDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkoutSet
    template_name = 'sets/set_confirm_delete.html'

    def get_queryset(self):
        return WorkoutSet.objects.filter(exercise__workout__user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Set deleted successfully.')
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('workout-detail', args=[self.object.exercise.workout.pk])


@login_required
def progress_view(request):
    workouts = Workout.objects.filter(user=request.user)
    weight_logs = WeightLog.objects.filter(user=request.user)
    exercises = []
    for workout in workouts:
        for exercise in workout.exercises.all():
            exercises.append(exercise)

    all_sets = WorkoutSet.objects.filter(exercise__workout__user=request.user)
    heaviest_set = all_sets.order_by('-weight').first()
    highest_reps = all_sets.order_by('-repetitions').first()
    highest_volume = all_sets.order_by('-weight', '-repetitions').first()
    personal_records = [
        {'label': 'Best Weight', 'value': f"{heaviest_set.weight} kg" if heaviest_set else '—'},
        {'label': 'Highest Reps', 'value': str(highest_reps.repetitions) if highest_reps else '—'},
        {'label': 'Highest Volume', 'value': f"{highest_volume.weight * highest_volume.repetitions} kg·reps" if highest_volume else '—'},
    ]

    exercise_progress = []
    for exercise in exercises:
        sets = exercise.sets.all().order_by('exercise__workout__workout_date')
        if sets.exists():
            exercise_progress.append({
                'name': exercise.exercise_name,
                'labels': [str(set.exercise.workout.workout_date) for set in sets],
                'values': [float(set.weight) for set in sets],
            })

    context = {
        'weight_logs': weight_logs,
        'workouts': workouts,
        'exercises': exercises,
        'personal_records': personal_records,
        'exercise_progress': exercise_progress,
    }
    return render(request, 'progress.html', context)


@login_required
def partner_view(request):
    partner_form = PartnerForm(user=request.user)
    partner_requests = Partner.objects.filter(Q(user=request.user) | Q(partner_user=request.user)).order_by('-created_at')
    accepted_partner = Partner.objects.filter(Q(user=request.user, status='accepted') | Q(partner_user=request.user, status='accepted')).first()
    if request.method == 'POST':
        partner_form = PartnerForm(request.user, request.POST)
        if partner_form.is_valid():
            target_user = partner_form.cleaned_data['partner_username']
            partner_user = get_object_or_404(__import__('django.contrib.auth').contrib.auth.get_user_model(), username=target_user)
            Partner.objects.create(user=request.user, partner_user=partner_user)
            messages.success(request, 'Partner request sent.')
            return redirect('partner')
    related_user = None
    if accepted_partner:
        related_user = accepted_partner.partner_user if accepted_partner.user == request.user else accepted_partner.user
    context = {
        'partner_form': partner_form,
        'partner_requests': partner_requests,
        'accepted_partner': accepted_partner,
        'related_user': related_user,
        'partner_workouts': Workout.objects.filter(user=related_user).order_by('-workout_date', '-created_at')[:3] if related_user else [],
        'partner_weight_logs': WeightLog.objects.filter(user=related_user).order_by('-date', '-created_at')[:3] if related_user else [],
    }
    return render(request, 'partner.html', context)


@login_required
def accept_partner_request(request, pk):
    partner_request = get_object_or_404(Partner, pk=pk)
    if partner_request.partner_user != request.user:
        messages.error(request, 'You cannot accept this request.')
        return redirect('partner')
    partner_request.status = 'accepted'
    partner_request.save()
    messages.success(request, 'Partner request accepted.')
    return redirect('partner')


@login_required
def decline_partner_request(request, pk):
    partner_request = get_object_or_404(Partner, pk=pk)
    if partner_request.partner_user != request.user and partner_request.user != request.user:
        messages.error(request, 'You cannot manage this request.')
        return redirect('partner')
    partner_request.status = 'declined'
    partner_request.save()
    messages.success(request, 'Partner request declined.')
    return redirect('partner')
