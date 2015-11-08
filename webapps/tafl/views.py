from django.shortcuts import render, redirect
#from ws4redis.publisher import RedisPublisher
#from ws4redis.redis_store import RedisMessage

from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate

from tafl.models import *
from tafl.forms import *

#@login_required
def gamespage(request):
    return render(request, "tafl/mainpage.html")

#@login_required
def makegame(request):
    return None

#@login_required
def joingame(request):
    return None

#@login_required
def usersearch(request):
    return None

#@login_required
def profile(request):
    return None

#@login_required
def about(request):
    return render(request, "tafl/about.html")

def register(request):
    return redirect('/tafl/')
