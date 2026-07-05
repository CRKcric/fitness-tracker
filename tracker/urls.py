from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('workouts/', views.WorkoutListView.as_view(), name='workout-list'),
    path('workouts/new/', views.WorkoutCreateView.as_view(), name='workout-create'),
    path('workouts/<int:pk>/', views.WorkoutDetailView.as_view(), name='workout-detail'),
    path('workouts/<int:pk>/edit/', views.WorkoutUpdateView.as_view(), name='workout-edit'),
    path('workouts/<int:pk>/delete/', views.WorkoutDeleteView.as_view(), name='workout-delete'),
    path('workouts/<int:pk>/duplicate/', views.duplicate_workout, name='workout-duplicate'),
    path('weight/', views.WeightLogListView.as_view(), name='weight-list'),
    path('weight/new/', views.WeightLogCreateView.as_view(), name='weight-create'),
    path('weight/<int:pk>/edit/', views.WeightLogUpdateView.as_view(), name='weight-edit'),
    path('weight/<int:pk>/delete/', views.WeightLogDeleteView.as_view(), name='weight-delete'),
    path('sets/<int:pk>/edit/', views.WorkoutSetUpdateView.as_view(), name='set-edit'),
    path('sets/<int:pk>/delete/', views.WorkoutSetDeleteView.as_view(), name='set-delete'),
    path('progress/', views.progress_view, name='progress'),
    path('partner/', views.partner_view, name='partner'),
    path('partner/accept/<int:pk>/', views.accept_partner_request, name='accept-partner'),
    path('partner/decline/<int:pk>/', views.decline_partner_request, name='decline-partner'),
]
