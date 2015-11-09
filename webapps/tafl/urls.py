from django.conf.urls import include, url

urlpatterns = [
    url(r'^$', 'tafl.views.gamespage', name='games'),
    url(r'^game$', 'tafl.views.game', name='game'),
    url(r'^login$', 'django.contrib.auth.views.login', {'template_name':'tafl/login.html'}),
    url(r'^logout%', 'django.contrib.auth.views.logout_then_login', name='logout'),
    #but wait there's more :O
]
