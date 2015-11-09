from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

now = timezone.now()

class Player(models.Model):
    user = models.ForeignKey(User)
    cur_game = models.ForeignKey('Game', blank=True, null=True)
    rank = models.IntegerField(default=0)

    def __unicode__(self):
        return self.user.username

class Game(models.Model):
    black_player = models.ForeignKey('Player', related_name='black_games', blank=True, null=True)
    white_player = models.ForeignKey('Player', related_name='white_games', blank=True, null=True)
    waiting_player = models.ForeignKey('Player', related_name='waiting_games', blank=True, null=True)
    # ^ A holding spot for when we know a player is waiting in a game, but 
    # we don't know what color they are yet. 
    players = models.ManyToManyField('Player', related_name="games", blank=True)
    turn = models.BooleanField()
    # history = Move list (Future expansion idea)
    ruleset = models.ForeignKey('Ruleset')
    winner = models.ForeignKey('Player', related_name='won_games', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return str(self.players.all())

class Piece(models.Model):
    game = models.ForeignKey('Game', related_name='pieces')
    PIECE_TYPES = (
        ('KING', 'King'),
        ('PAWN', 'Pawn'),
    )
    p_type = models.CharField(choices=PIECE_TYPES, max_length=4)
    PIECE_COLORS = (
        ('BL', 'Black'),
        ('WH', 'White'),
    )
    color = models.CharField(choices=PIECE_COLORS, max_length=2)

    def __unicode__(self):
        return self.color + ": " + self.p_type

class Square(models.Model):
    game = models.ForeignKey('Game', related_name='squares')
    x_coord = models.IntegerField()
    y_coord = models.IntegerField()
    member = models.ForeignKey('Piece', blank=True, null=True)

    def __unicode__(self):
        return str(self.pk) + ": (" + str(self.x_coord) + ", " + str(self.y_coord) + ")"

class Ruleset(models.Model):
    name = models.CharField(max_length=40)
    pieces = models.CharField(max_length=1000)
    WIN_CONDITIONS = (
        ('CORNER', 'Corner escape'),
        ('EDGE', 'Edge escape'),
    )
    win_cond = models.CharField(choices=WIN_CONDITIONS, max_length=6)
    size = models.IntegerField()

    def __unicode__(self):
        return self.name

class ChatMessage(models.Model):
    player = models.ForeignKey('Player')
    text = models.CharField(max_length=400)
    time = models.DateTimeField()

    def __unicode__(self):
        return self.player.user.teamname + ": " + self.text[:20]
