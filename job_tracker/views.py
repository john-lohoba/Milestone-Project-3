from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.views import generic
from datetime import date, timedelta
from .forms import CompletedJobForm, AbsenceForm, ProfileForm
from .models import CompletedJob, Absence, ProfileTarget

# Create your views here.

def job_tracker(request):
    user = request.user
    today = date.today()
    start_of_week = today - timedelta(days= today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Dynamic rostered days
    current_week = [start_of_week + timedelta(days=i) for i in range(7)]
    rostered_days_off = user.profiletarget.days_off
    working_days_raw = [d for d in current_week if d.strftime("%a") not in rostered_days_off]
    working_days = []
    for d in working_days_raw:
        working_days.append(d.strftime("%a"))

    # Creates dict with the completed jobs of the current week {date:credits}
    jobs = CompletedJob.objects.filter(user= user, completed_on__in= working_days_raw).values('completed_on').annotate(total_credits=Sum('job_type__credits'))
    credits_by_day = {d:0 for d in working_days_raw}
    for entry in jobs:
        if entry['completed_on'] in credits_by_day:
            credits_by_day[entry['completed_on']] = float(entry["total_credits"])
    
    # Gets user's absences for current week and creates dict with the day and duration
    absences = Absence.objects.filter(user = user, date__range=(start_of_week, end_of_week))
    absences_by_day = {a.date: float(a.duration) for a in absences if a.date in working_days_raw}
    
    # Calculates target and creates dict with day and the target
    daily_target = float(user.profiletarget.daily_target)
    shift_hours = float(user.profiletarget.daily_hours)
    # Adjusts daily target for users that are not on a standard 8h shift. 
    adjusted_daily_target = (shift_hours * daily_target)/8
    adjusted_targets = {}
    for current_day in working_days_raw:
        absence = absences_by_day.get(current_day, 0)
        adjusted = round(((shift_hours - absence) * adjusted_daily_target) / shift_hours, 2)
        adjusted_targets[current_day] = adjusted
    
    # Store all of the combined metrics for the week
    weekly_data = []
    for current_day in working_days_raw:
        weekly_data.append({
            "date": current_day.strftime("%a %d. %b"),
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
    target = float(request.user.profiletarget.daily_target)
    daily_hours = float(request.user.profiletarget.daily_hours)
    days_off = request.user.profiletarget.days_off
    profile_obj = request.user.profiletarget
    profile_form = ProfileForm()
    return render(
        request,
        "job_tracker/profile.html",
        {
        "target": target,
        "daily_hours": daily_hours,
        "days_off": days_off,
        "profile_obj": profile_obj,
        "profile_form": profile_form,
    })


def profile_edit(request, pk):
    if request.method == "POST":
        target = get_object_or_404(ProfileTarget, pk=pk)
        profile_form = ProfileForm(data=request.POST, instance=target)
        if profile_form.is_valid():
            form = profile_form.save(commit=False)
            form.user = request.user
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Settings updated')
        else:
            messages.add_message(request, messages.SUCCESS, 'Error updating settings')

    return redirect('profile')
