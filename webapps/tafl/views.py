from django.shortcuts import render

def gamespage(request):
    return render(request, "tafl/mainpage.html")
