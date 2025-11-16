from django.db.models import Sum, DecimalField
from django.db.models.functions import TruncWeek, TruncDate
from django.shortcuts import render
from datetime import timedelta
from job_tracker.models import CompletedJob, Absence
from collections import defaultdict

# Create your views here.


def week_history(request):
    user = request.user
    daily_target = float(user.profiletarget.daily_target)
    shift_hours = float(user.profiletarget.daily_hours)
    adjusted_target = float((shift_hours * daily_target) / 8)
    rostered_days_off = user.profiletarget.days_off

    jobs_by_week = (
        CompletedJob.objects.filter(user=user)
        .annotate(week_start=TruncWeek("completed_on"))
        .values("week_start")
        .annotate(total_credits=Sum("job_type__credits", output_field=DecimalField()))
        .order_by("-week_start")
    )

    absences_by_week = (
        Absence.objects.filter(user=user)
        .annotate(week_start=TruncWeek("date"))
        .values("week_start")
        .annotate(total_absence=Sum("duration", output_field=DecimalField()))
        .order_by("-week_start")
    )
    absence_dict = {
        item["week_start"]: item["total_absence"] for item in absences_by_week
    }

    jobs_by_day = (
        CompletedJob.objects.filter(user=user)
        .annotate(week_start=TruncWeek("completed_on"), day=TruncDate("completed_on"))
        .values("week_start", "day", "job_type__name")
        .order_by("-week_start", "day")
    )
    jobs_dict = defaultdict(list)

    for job in jobs_by_day:
        # Convert date to weekday name (e.g. "Monday")
        day_name = job["day"].strftime("%A")
        job_name = job["job_type__name"]
        jobs_dict[day_name].append(job_name)

    # Optionally, convert defaultdict to a regular dict
    jobs_by_week_array = dict(jobs_dict)

    # weeks dict
    weeks = []
    seen_weeks = set()
    for job in jobs_by_week:
        week_start = job["week_start"]
        if week_start in seen_weeks:
            continue
        seen_weeks.add(week_start)

        credits = job["total_credits"] or 0
        absence = absence_dict.get(week_start, 0) or 0
        current_week = [week_start + timedelta(days=i) for i in range(7)]
        rostered_days = [
            d for d in current_week if d.strftime("%a") not in rostered_days_off
        ]
        weekly_target = adjusted_target * len(rostered_days)
        target = round(weekly_target - float(absence), 2)
        update = round(float(credits) - target, 2)

        week_jobs = (
            CompletedJob.objects.filter(
                user=user,
                completed_on__gte=week_start,
                completed_on__lte=week_start + timedelta(days=6),
            )
            .annotate(day=TruncDate("completed_on"))
            .values("day", "job_type__name")
            .order_by("day")
        )

        # Group jobs by weekday name
        jobs_by_day = defaultdict(list)
        for j in week_jobs:
            jobs_by_day[j["day"].strftime("%A")].append(j["job_type__name"])

        jobs_by_day_complete = {
            d.strftime("%A"): jobs_by_day.get(d.strftime("%A"), [])
            for d in rostered_days
        }

        weeks.append(
            {
                "monday": week_start,
                "sunday": week_start + timedelta(days=6),
                "current_week": current_week,
                "total_credits": round(credits, 2),
                "total_absence": round(absence, 2),
                "target": target,
                "update": update,
                "rostered_days": rostered_days,
                "jobs_by_day": jobs_by_day_complete,
            }
        )

    return render(
        request,
        "week_history/week_history.html",
        {
            "weeks": weeks,
            "jobs_by_week_array": jobs_by_week_array,
        },
    )
