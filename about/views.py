from django.shortcuts import render
from .models import About

# Create your views here.


def about_us(request):
    return render(request, "about/about.html")
