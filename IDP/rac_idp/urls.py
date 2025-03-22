from django.urls import path
from . import views
from .views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
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

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)