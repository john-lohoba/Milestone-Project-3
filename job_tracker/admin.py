from django.contrib import admin
from .models import JobType, CompletedJob, Absence, ProfileTarget

# Register your models here.

admin.site.register(JobType)
admin.site.register(CompletedJob)
admin.site.register(Absence)
admin.site.register(ProfileTarget)
