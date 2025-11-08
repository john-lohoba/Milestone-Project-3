from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.views import generic
from datetime import date, timedelta
from .forms import CompletedJobForm, AbsenceForm, ProfileForm
from .models import CompletedJob, Absence, ProfileTarget

# Create your views here.


def job_tracker(request):
    """
    Renders the users performance metrics for the current week.
    Displays an agregated data from :model:`CompletedJob`,
    :model:`ProfileTarget and :model:`Absence`.

    **Context**

    `weekly_data`
        an instance of all the agragated data from
        :model:`ProfileTarget`, :model:`CompletedJob` and
        :model:`Absence`.
    `job_form`
        an instance of :form:`.forms.CompletedJobForm`

    **Template**
    :template:`job_tracker/job-tracker.html`
    """
    user = request.user
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    job_form = CompletedJobForm()

    # Dynamic rostered days
    current_week = [start_of_week + timedelta(days=i) for i in range(7)]
    rostered_days_off = user.profiletarget.days_off
    working_days_raw = [
        d for d in current_week if d.strftime("%a") not in rostered_days_off
    ]
    working_days = []
    for d in working_days_raw:
        working_days.append(d.strftime("%a"))

    # Creates dict with the completed jobs of the current week {date:credits}
    jobs = (
        CompletedJob.objects.filter(user=user, completed_on__in=working_days_raw)
        .values("completed_on")
        .annotate(total_credits=Sum("job_type__credits"))
    )
    credits_by_day = {d: 0.00 for d in working_days_raw}
    for entry in jobs:
        if entry["completed_on"] in credits_by_day:
            credits_by_day[entry["completed_on"]] = float(entry["total_credits"])

    # Gets users absences for current week and creates dict with day & duration
    absences = Absence.objects.filter(
        user=user, date__range=(start_of_week, end_of_week)
    )
    absences_by_day = {
        a.date: float(a.duration) for a in absences if a.date in working_days_raw
    }

    # Calculates target and creates dict with day and the target
    daily_target = float(user.profiletarget.daily_target)
    shift_hours = float(user.profiletarget.daily_hours)
    # Adjusts daily target for users that are not on a standard 8h shift.
    adjusted_daily_target = (shift_hours * daily_target) / 8
    adjusted_targets = {}
    for current_day in working_days_raw:
        absence = absences_by_day.get(current_day, 0)
        adjusted = round(
            ((shift_hours - absence) * adjusted_daily_target) / shift_hours, 2
        )
        adjusted_targets[current_day] = adjusted

    # Store all of the combined metrics for the week
    weekly_data = []
    for current_day in working_days_raw:
        weekly_data.append(
            {
                "date": current_day.strftime("%a %d. %b"),
                "target": adjusted_targets[current_day],
                "credits": credits_by_day[current_day],
            }
        )

    return render(
        request,
        "job_tracker/job-tracker.html",
        {
            "weekly_data": weekly_data,
            "job_form": job_form,
        },
    )


def job_post(request):
    """
    Display an individual :model:`CompletedJob`.

    **Context**
    `job_form`
        an instance of :form:`CompletedJobForm`
    """
    if request.method == "POST":
        job_form = CompletedJobForm(request.POST)
        if job_form.is_valid():
            form = job_form.save(commit=False)
            form.user = request.user
            form.save()
            messages.add_message(request, messages.SUCCESS, "New job submitted")
            return redirect("tracker")
    else:
        job_form = CompletedJob()

    return render(request, "jobs/job_form.html", {"job_form": job_form})


class CompletedJobList(generic.ListView):
    """
    Renders a list of the users completed jobs.
    Display instances of :model:`CompletedJob`,
    related to the user.

    **Context**
    `job_form`
        an instance of :form:`CompletedJobForm`

    **Template**
    :template:`job_tracker/job-history.html"
    """

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
        context["job_form"] = CompletedJobForm()
        return context


def job_edit(request, pk):
    """
    Display an individual job for edit.

    **Context**
    `job`
        a single completed job related to the user.
    `job_form`
        an instance of :form:`CompletedJobForm`.
    """
    if request.method == "POST":
        job = get_object_or_404(CompletedJob, pk=pk)
        job_form = CompletedJobForm(data=request.POST, instance=job)
        if job_form.is_valid():
            form = job_form.save(commit=False)
            form.user = request.user
            form.save()
            messages.add_message(request, messages.SUCCESS, "Job Updated")
            return redirect("job-history")

        else:
            messages.add_message(request, messages.ERROR, "Error updatng job")
    return redirect("job-history")


def job_delete(request, pk):
    """
    Delete an individual job

    **Context**
    `job`
        a single completed job related to the user.
    """
    job = get_object_or_404(CompletedJob, pk=pk)
    if job.user == request.user:
        job.delete()
        messages.add_message(request, messages.SUCCESS, "Job Deleted")
    else:
        messages.add_message(request, messages.ERROR, "Error deleting job")

    return redirect("job-history")


class AbsencesList(generic.ListView):
    """
    Renders a list of the users absences.
    Displays instances of :model:`Absence` related to the user.

    **Context**
    `absence_form`
        an instance of :form:`AbsenceForm`.

    **Template**
    :template:`job_tracker/absences.html`.
    """

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
        context["absence_form"] = AbsenceForm()
        context["absence_edit_form"] = AbsenceForm(prefix="edit")
        return context


def absence_post(request):
    """
    Display an individual :model:`Absence`

    **Context**
    `absence_form`
        an instance of :form:`AbsenceForm`
    """
    if request.method == "POST":
        absence_form = AbsenceForm(request.POST)
        if absence_form.is_valid():
            form = absence_form.save(commit=False)
            form.user = request.user
            form.save()
            messages.add_message(request, messages.SUCCESS, "New absence submitted")
        else:
            messages.add_message(request, messages.ERROR, "Error sumbitting absence")
    return redirect("absences")


def absence_edit(request, pk):
    """
    Display a single absence for edit.
    **Context**

    `absence`
        a single absence related to the user.
    `absence_form`
        an instance of :form:`AbsenceForm`.
    """
    if request.method == "POST":
        absence = get_object_or_404(Absence, pk=pk)
        absence_edit_form = AbsenceForm(
            data=request.POST, instance=absence, prefix="edit"
        )
        if absence_edit_form.is_valid():
            form = absence_edit_form.save(commit=False)
            form.user = request.user
            form.save()
            messages.add_message(request, messages.SUCCESS, "Absence Updated")
        else:
            messages.add_message(request, messages.ERROR, "Error updating absence")
    return redirect("absences")


def absence_delete(request, pk):
    """
    Delete an individual absence
    **Context**

    `absence`
        a single absence related to the user.
    """
    absence = get_object_or_404(Absence, pk=pk)
    if absence.user == request.user:
        absence.delete()
        messages.add_message(request, messages.SUCCESS, "Absence deleted")
    else:
        messages.add_message(request, messages.ERROR, "Error deleting absence")

    return redirect("absences")


def profile(request):
    """
    Render the users profile settings.
    Displays an instance of :model:`ProfileTarget`
    **Context**

    `target`
        target related to the user from :model:`ProfileTarget`.
    `daily_hours`
        daily working hours related to the user from :model:`ProfileTarget`.
    `days_off`
        rostered days off related to the user from :model:`ProfileTarget`.
    `profile_obj`
        instance of :model:`ProfileTarget`.
    `profile_form`
        instance of :form:`ProfileForm`.

    **Template**
    :template:`job_tracker/profile.html`.
    """
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
        },
    )


def profile_edit(request, pk):
    """
    Display the users Profile settings for edit from :model:`ProfileTarget`.
    **Context**

    `target`
        the target related to the user.
    `profile_form`
        an instance of :form:`ProfileForm.
    """
    if request.method == "POST":
        target = get_object_or_404(ProfileTarget, pk=pk)
        profile_form = ProfileForm(data=request.POST, instance=target)
        if profile_form.is_valid():
            form = profile_form.save(commit=False)
            form.user = request.user
            form.save()
            messages.add_message(request, messages.SUCCESS, "Settings updated")
        else:
            messages.add_message(request, messages.SUCCESS, "Error updating settings")

    return redirect("profile")
