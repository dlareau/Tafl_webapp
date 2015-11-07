from django.conf.urls import include, url

urlpatterns = [
    url(r'^$', 'tafl.views.gamespage', name='games'),
    url(r'^register$', 'tafl.views.register', name='register'),
    url(r'^login$', 'tafl.views.login', name='login'),
    url(r'^logout$', 'django.contrib.auth.views.logout_then_login', name='logout'),
    url(r'^makegame$', 'tafl.views.makegame', name='makegame'),
    url(r'^joingame$', 'tafl.views.joingame', name='joingame'),
    url(r'^profile', 'tafl.views.profile', name='view'),
]
