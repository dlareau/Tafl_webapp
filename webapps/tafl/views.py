from django.shortcuts import render, redirect
#from ws4redis.publisher import RedisPublisher
#from ws4redis.redis_store import RedisMessage

from django.http import Http404, HttpResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate

from itertools import chain

from tafl.models import *
from tafl.forms import *

@login_required
def gamespage(request):
    context = {}

    currUser = request.user
    context['user'] = currUser

    #sort - having migration issues, so commenting this out for now
    #sortby = request.GET.get('sortby')
    #if sortby == 'time' or not sortby:
    #    # by time is default
    #    games = Game.objects.all().order_by('-time')
    #if sortby == 'rank':
    #    games = Game.objects.all().order_by('waiting_player__rank')
    #if sortby == 'color':
    #    #citation for __isnull
    #    #stackoverflow.com/questions/14831327/in-a-django-queryset-how-to-
    #        # filter-for-not-exists-in-a-many-to-one-relationsh
    #    bgames = Game.objects.filter(black_player__isnull=False)
    #    wgames = Game.objects.filter(white_player__isnull=False)
    #    ugames = Game.objects.filter(black_player__isnull=True).filter(white_player__isnull=True)
    #    #citation for itertools chain: 
    #    #stackoverflow.com/questions/431628/how-to-combine-2-or-more-querysets-in-a-django-view
    #    games = chain(bgames, wgames, ugames)
    #if sortby == 'variant':
    #    games = Game.objects.all() #bc rn there's only tablut - implement actual sorting later
    #    
    context['games'] = Game.objects.all()
    return render(request, "tafl/mainpage.html", context)

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
    context = {}

    # user making the request so their profile link in navbar works
    currUser = request.user
    context['user'] = currUser

    # user whose profile we want to load
    profUser = User.objects.get(username=request.GET.get('un'))
    context['puser'] = profUser
    player = Player.objects.get(user=profUser)
    context['rank'] = player.rank

    # get stats
    wt = Game.objects.filter(white_player=player).count()
    context['whitetotal'] = wt
    ww = Game.objects.filter(white_player=player).filter(winner=player).count()
    context['whitewin'] = ww
    wl = wt - ww
    context['whitelose'] = wl

    bt = Game.objects.filter(black_player=player).count()
    context['blacktotal'] = bt
    bw = Game.objects.filter(black_player=player).filter(winner=player).count()
    context['blackwin'] = bw
    bl = bt - bw
    context['blacklose'] = bl

    context['overallwin'] = ww + bw
    context['overalllose'] = wl + bl
    context['overalltotal'] = wt + bt
    return render(request, "tafl/profile.html", context)

@login_required
def about(request):
    return render(request, "tafl/about.html")

def mylogin(request):
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

    user = authenticate(username=form.cleaned_data['username'], 
                        password=form.cleaned_data['password'])
    if user is not None and user.is_active:
        login(request, user)
        return redirect('/tafl/')
    
    context['rform'] = RegistrationForm()
    return render(request, "tafl/login.html", context)

def mylogout(request):
    logout(request)
    context = {}
    context['lform'] = LoginForm()
    context['rform'] = RegistrationForm()
    return render(request, "tafl/login.html", context)

@transaction.atomic
def register(request):
    context = {}
    form = RegistrationForm(request.POST)
    context['rform'] = form

    if not form.is_valid():
        context['lform'] = LoginForm()
        return render(request, "tafl/login.html", context)

    #create user
    newUser = User.objects.create_user(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'],
                                    email=form.cleaned_data['email'])
    newUser.save()

    #create player
    newPlayer = Player(user=newUser, cur_game=None)
    newPlayer.save()
    
    #log them in
    newUser = authenticate(username=form.cleaned_data['username'],
                           password=form.cleaned_data['password1'])
    login(request, newUser)
    return redirect('/tafl/')
