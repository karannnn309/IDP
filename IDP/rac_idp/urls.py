from django.urls import path
from . import views

urlpatterns = [
    path('', views.submit_application, name='submit_application'),  # Form submission page
    path('results/<int:applicant_id>/', views.applicant_results, name='results'),  # Show mismatches & extracted data
]

