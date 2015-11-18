from django.shortcuts import render, redirect
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage

from django.http import Http404, HttpResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
import json

from itertools import chain
import random

from tafl.redis import *
from tafl.models import *
from tafl.forms import *
import tafl.game

@login_required
def gamespage(request):
    context = {}

    currUser = request.user
    context['user'] = currUser

    sortby = request.GET.get('sortby')
    #citation for __isnull
    #stackoverflow.com/questions/14831327/in-a-django-queryset-how-to-
       # filter-for-not-exists-in-a-many-to-one-relationsh
    if sortby == 'time' or not sortby:
        print "sortby time"
        # by time is default
        games = Game.objects.filter(waiting_player__isnull=False).order_by('timestamp')
    if sortby == 'rank':
        print "sortby rank"
        games = Game.objects.filter(waiting_player__isnull=False).order_by('waiting_player__rank')
    if sortby == 'color':
        print "sortby color"
        games = Game.objects.filter(waiting_player__isnull=False).order_by('waitingcolor')
        
        #bgames = Game.objects.filter(black_player__isnull=False)
        #wgames = Game.objects.filter(white_player__isnull=False)
        #ugames = Game.objects.filter(black_player__isnull=True).filter(white_player__isnull=True)
        #citation for itertools chain: 
        #stackoverflow.com/questions/431628/how-to-combine-2-or-more-querysets-in-a-django-view
        #games = chain(bgames, wgames, ugames)
    if sortby == 'variant':
        print "sortby variant"
        #bc rn there's only tablut - implement actual sorting later
        games = Game.objects.filter(waiting_player__isnull=False)
        
    context['games'] = games
    return render(request, "tafl/mainpage.html", context)

@login_required
@transaction.atomic
def game(request):
    # Get player
    p = Player.objects.get(user=request.user)
    # Post requests to game are move requests
    if(request.method == 'POST' and "move" in request.POST and request.POST["move"] != ""):
        # Get game and move
        move = json.loads(request.POST["move"])
        g = request.user.player_set.all()[0].cur_game

        # Check if move is valid
        if(not g.is_valid_move(move[0], move[1])):
            return HttpResponse("invalid 1")

        # Move was valid, check for other player and send the move update
        if(g.other_player(p) != None):
            send_move_update(g.other_player(p), move)

        # Check for capture and make capture
        # Check for win and do win things if appropriate

        # Commit move to database
        g.make_move(move[0], move[1])
        return HttpResponse("valid")

    if(p.cur_game == None):
        return redirect('/tafl/') 
    context = {'game':p.cur_game, 'player': p}
    return render(request, "tafl/gamepage.html", context)

@login_required
def makegame(request):
    if(request.method == 'POST'):
        form = GameForm(request.POST)
        if form.is_valid():
            ruleset = Ruleset.objects.get(name=form.cleaned_data['ruleset'])
            player = Player.objects.get(user=request.user)
            if(form.cleaned_data['optradio'] == "black"):
                g = tafl.game.make_game(ruleset, player, None, player)
            elif(form.cleaned_data['optradio'] == "white"):
                g = tafl.game.make_game(ruleset, None, player, player)
            elif(form.cleaned_data['optradio'] == "either"):
                g = tafl.game.make_game(ruleset, None, None, player)
            else:
                g = tafl.game.make_game(ruleset, None, None, player)

            player.cur_game = g;
            player.save()

    return redirect('/tafl/game')

@login_required
def joingame(request):
    context = {}

    usr = request.user
    player = Player.objects.get(user=usr)
    gameid = request.POST['gameid']
    g = Game.objects.get(pk=gameid)

    #set player 2
    if g.black_player != None:
        g.white_player = player
    elif g.white_player != None:
        g.black_player = player
    else: #either case, for now randomly assign
        coinflip = random.randint(0,1)
        if coinflip:
            g.white_player = player
            g.black_player = g.waiting_player
        else:
            g.white_player = g.waiting_player
            g.black_player = player

    g.waiting_player = None #cleanup
    player.cur_game = g

    g.save()
    player.save()

    return redirect('/tafl/game') 

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

@login_required
@transaction.atomic
def resign(request):
    p = Player.objects.get(user=request.user)
    p2 = p.cur_game.other_player(p)
    if(p2 != None):
        p.cur_game.winner = p2
        p.cur_game.save()
        p2.cur_game = None
        p2.save()
    p.cur_game = None
    p.save()
    return redirect('/tafl/') 
