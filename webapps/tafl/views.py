from django.shortcuts import render
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage

def gamespage(request):
    return render(request, "tafl/mainpage.html")

def makegame(request):
    return None

def joingame(request):
    return None

def profile(request):
    return None

def register(request):
    return None
