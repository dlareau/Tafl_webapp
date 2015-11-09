from django.shortcuts import render
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage

def gamespage(request):
    return render(request, "tafl/mainpage.html")

def game(request):
    return render(request, "tafl/gamepage.html")
