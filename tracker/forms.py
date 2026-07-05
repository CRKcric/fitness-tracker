from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Exercise, Partner, WeightLog, Workout, WorkoutSet

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with that email already exists.')
        return email

    def clean_password2(self):
        password2 = self.cleaned_data.get('password2')
        if password2:
            validate_password(password2, self.instance)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with that email already exists.')
        return email


class WorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        fields = ('workout_name', 'workout_date', 'notes')
        widgets = {
            'workout_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_workout_date(self):
        workout_date = self.cleaned_data.get('workout_date')
        if workout_date and workout_date > timezone.now().date():
            raise forms.ValidationError('Workout date cannot be in the future.')
        return workout_date


class ExerciseForm(forms.ModelForm):
    exercise_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'list': 'common-exercises'}))

    class Meta:
        model = Exercise
        fields = ('exercise_name', 'category', 'display_order')


class WorkoutSetForm(forms.ModelForm):
    class Meta:
        model = WorkoutSet
        fields = ('exercise', 'set_number', 'weight', 'repetitions', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, workout=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if workout is not None:
            self.fields['exercise'].queryset = workout.exercises.all()
        else:
            self.fields['exercise'].queryset = Exercise.objects.none()

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None and weight <= 0:
            raise ValidationError('Weight must be greater than zero.')
        return weight

    def clean_repetitions(self):
        repetitions = self.cleaned_data.get('repetitions')
        if repetitions is not None and repetitions <= 0:
            raise ValidationError('Repetitions must be greater than zero.')
        return repetitions


class WeightLogForm(forms.ModelForm):
    class Meta:
        model = WeightLog
        fields = ('date', 'body_weight')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_body_weight(self):
        body_weight = self.cleaned_data.get('body_weight')
        if body_weight is not None and body_weight <= 0:
            raise ValidationError('Body weight must be greater than zero.')
        return body_weight


class PartnerForm(forms.Form):
    partner_username = forms.CharField(max_length=150, label='Partner username')

    def clean_partner_username(self):
        username = self.cleaned_data.get('partner_username')
        if not username:
            return username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValidationError('No user found with that username.')
        if user == self.user:
            raise ValidationError('You cannot partner with yourself.')
        if Partner.objects.filter(user=self.user, partner_user=user).exists() or Partner.objects.filter(user=user, partner_user=self.user).exists():
            raise ValidationError('A partnership request already exists with this user.')
        return username

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
