from django import forms
from .models import CompletedJob, Absence, ProfileTarget

class CompletedJobForm(forms.ModelForm):
    """
    Form class for users to submit completed jobs.
    """
    class Meta:
        model = CompletedJob
        fields = ('job_type', 'completed_on')
        widgets = {'completed_on': forms.DateInput(attrs={'type': 'date'}),}


class AbsenceForm(forms.ModelForm):
    """
    Form class for users to record absences.
    """
    class Meta:
        model = Absence
        fields = ('duration', 'date')
        widgets = {'date': forms.DateInput(attrs={'type': 'date'}),}


class ProfileForm(forms.ModelForm):
    """
    Form class for users to modify their profile settings.
    """
    days_off = forms.MultipleChoiceField(choices=ProfileTarget.DAYS_OF_WEEK, widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = ProfileTarget
        fields = ('daily_target','daily_hours','days_off')