from django.shortcuts import render, redirect
#from ws4redis.publisher import RedisPublisher
#from ws4redis.redis_store import RedisMessage

from django.http import Http404, HttpResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate

from tafl.models import *
from tafl.forms import *

@login_required
def gamespage(request):
    return render(request, "tafl/mainpage.html")

@login_required
def makegame(request):
    return None

@login_required
def joingame(request):
    return None

@login_required
def usersearch(request):
    return None

@login_required
def profile(request):
    return render(request, "tafl/profile.html")

@login_required
def about(request):
    return render(request, "tafl/about.html")

def login(request):
    context = {}
    if request.method == "GET":
        context['lform'] = LoginForm()
        context['rform'] = RegistrationForm()
        return render(request, "tafl/login.html", context)
    
    form = LoginForm(request.POST)
    context['lform'] = form
    
    if not form.is_valid():
        context['rform'] = RegistrationForm()
        return render(request, "tafl/login.html", context)

    

    return None

@transaction.atomic
def register(request):
    context = {}
    form = RegistrationForm(request.POST)
    context['rform'] = form

    if not form.is_valid():
        context['lform'] = LoginForm()
        return render(request, "tafl/login.html", context)

    #create user


    #create player

    

    return redirect('/tafl/')
