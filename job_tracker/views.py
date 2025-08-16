from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.views import generic
from datetime import date, timedelta
from .forms import CompletedJobForm, AbsenceForm
from .models import CompletedJob, Absence

# Create your views here.

def job_tracker(request):
    user = request.user
    today = date.today()
    start_of_week = today - timedelta(days= today.weekday())
    end_of_week = start_of_week + timedelta(days=4)

    jobs = CompletedJob.objects.filter(user = user, completed_on__range=
    (start_of_week, end_of_week)).values('completed_on').annotate(total_credits=Sum('job_type__credits'))
    
    # Creates dict with the completed jobs of the current week {date:credits}
    credits_by_day = {start_of_week + timedelta(days=i): 0 for i in range(7)}
    for entry in jobs:
        credits_by_day[entry['completed_on']] = float(entry["total_credits"])
    
    # Gets user's absences for current week and creates dict with the day and duration
    absences = Absence.objects.filter(user = user, date__range=(start_of_week, end_of_week))
    absences_by_day = {a.date: float(a.duration) for a in absences}
    
    # Calculates target and creates dict with day and the target
    daily_target = float(user.profiletarget.daily_target)
    adjusted_targets = {}
    shift_hours = 8
    for i in range(5):
        current_day = start_of_week + timedelta(days=i)
        absence = absences_by_day.get(current_day, 0)
        adjusted = round(((shift_hours - absence) * daily_target) / shift_hours, 2)
        adjusted_targets[current_day] = adjusted
    
    # Store all of the combined metrics for the week
    weekly_data = []
    for i in range(5):
        current_day = start_of_week + timedelta(days=i)
        weekly_data.append({
            "date": current_day,
            "target": adjusted_targets[current_day],
            "credits": credits_by_day[current_day]
        })
    
    # Create a form for submitting completed jobs
    if request.method == "POST":
        job_form = CompletedJobForm(request.POST)
        if job_form.is_valid():
            form = job_form.save(commit=False)
            form.user = user
            form.save()
            messages.add_message(request, messages.SUCCESS, 'New job submitted')
            return redirect('tracker')

    job_form = CompletedJobForm()
    return render(
        request,
        "job_tracker/job-tracker.html",
        {"weekly_data": weekly_data,
         "job_form": job_form,
         })


class CompletedJobList(generic.ListView):
    model = CompletedJob
    template_name = "job_tracker/job-history.html"
    paginate_by = 7

    def get_queryset(self):
        return CompletedJob.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        self.job_id = kwargs.get("job_id")
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job_form'] = CompletedJobForm()
        return context


def job_edit(request, pk):
    if request.method == "POST":
        job = get_object_or_404(CompletedJob, pk=pk)
        job_form = CompletedJobForm(data=request.POST, instance=job)
        if job_form.is_valid():
            form = job_form.save(commit=False)
            form.user = request.user
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Job Updated')
            return redirect('job-history')
        
        else:
            messages.add_message(request, messages.ERROR, 'Error updatng job')
    return redirect('job-history')


def job_delete(request, pk):
    job = get_object_or_404(CompletedJob, pk=pk)
    if job.user == request.user:
        job.delete()
        messages.add_message(request, messages.SUCCESS, 'Job Deleted')
    else:
        messages.add_message(request, messages.ERROR, "Error deleting job")
    
    return redirect('job-history')


class AbsencesList(generic.ListView):
    model = Absence
    template_name = "job_tracker/absences.html"
    paginate_by = 7

    def get_queryset(self):
        return Absence.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        self.absence_id = kwargs.get("absence_id")
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['absence_form'] = AbsenceForm()
        return context


def absence_post(request):
    if request.method == "POST":
        absence_form = AbsenceForm(request.POST)
        if absence_form.is_valid():
            form = absence_form.save(commit=False)
            form.user = request.user
            form.save()
            messages.add_message(request, messages.SUCCESS, 'New absence submitted')
        else:
            messages.add_message(request, messages.ERROR, 'Error sumbitting absence')

    return redirect('absences')


def absence_edit(request, pk):
    if request.method == "POST":
        absence = get_object_or_404(Absence, pk=pk)
        absence_form = AbsenceForm(data=request.POST, instance=absence)
        if absence_form.is_valid():
            form = absence_form.save(commit=False)
            form.user = request.user
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Absence Updated')
        else:
            messages.add_message(request, messages.ERROR, 'Error updating absence')
    
    return redirect('absences')


def absence_delete(request, pk):
    absence = get_object_or_404(Absence, pk = pk)
    if absence.user == request.user:
        absence.delete()
        messages.add_message(request, messages.SUCCESS, 'Absence deleted')
    else:
        messages.add_message(request, messages.ERROR, 'Error deleting absence')
    
    return redirect('absences')


def profile(request):
    return render(request, "job_tracker/profile.html")
