from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_tracker, name='tracker'),
    path('absences', views.AbsencesList.as_view(), name='absences'),
    path('absence/delete/<int:pk>', views.absence_delete, name='absence-delete'),
    path('absence/edit/<int:pk>', views.absence_edit, name='absence-edit'),
    path('absences/post', views.absence_post, name='absence-post'),
    path('history', views.CompletedJobList.as_view(), name='job-history'),
    path('history/update/<int:pk>', views.job_edit, name='update-completed-job'),
    path('history/delete/<int:pk>', views.job_delete, name='delete-completed-job'),
    path('profile',views.profile, name='profile'),
]