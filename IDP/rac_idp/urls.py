from django.urls import path
from . import views
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import login_view, otp_verification_view
from django.contrib.auth import views as auth_views  # Add this import


urlpatterns = [
    path("login/", login_view, name="login"),
    path("otp-verification/", otp_verification_view, name="otp_verification"),
    path("", views.landing_page, name="landing"),  # Landing Page
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Form submission and document verification
    path("apply/", views.submit_application, name="submit_application"),  # Form submission page
    path("verify_document/<int:applicant_id>/", views.verify_document, name="verify_document"),  # Document verification page

    # Results Page for a specific applicant (with applicant_id)
    path("results/<int:applicant_id>/", views.applicant_results, name="applicant_results"),
    path("view_results/<int:result_id>/", views.view_result, name="view_result"),

    # Applicant Dashboard (Can either be specific or generic)
    path("dashboard/", views.applicant_dashboard, name="applicant_dashboard"),  # Default dashboard for logged-in user
    
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset.html',
             email_template_name='auth/password_reset_email.html',
             subject_template_name='auth/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html',
             success_url='/password-reset/complete/'
         ), 
         name='password_reset_confirm'),
    path('password-reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)