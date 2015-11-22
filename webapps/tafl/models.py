from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

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
    waitingcolor = models.CharField(max_length=6)
    turn = models.BooleanField()
    # history = Move list (Future expansion idea)
    ruleset = models.ForeignKey('Ruleset')
    winner = models.ForeignKey('Player', related_name='won_games', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Returns true if there are no pieces between pos1 and pos2 (exclusive)
    def is_move_clear(self, pos1, pos2):
        if(pos1[0] == pos2[0]):
            max_y = max(pos1[1], pos2[1])
            min_y = min(pos1[1], pos2[1])
            return not self.pieces.filter(square__x_coord=pos1[0], 
                square__y_coord__gt=min_y, square__y_coord__lt=max_y).exists()
        if(pos1[1] == pos2[1]):
            max_x = max(pos1[0], pos2[0])
            min_x = min(pos1[0], pos2[0])
            return not self.pieces.filter(square__y_coord=pos1[1], 
                square__x_coord__gt=min_x, square__x_coord__lt=max_x).exists()
        return false

    # Returns true if the move is valid in the context of the current game
    def is_valid_move(self, pos1, pos2):
        if (self.is_move_clear(pos1, pos2) and not 
           (pos2[0] == self.ruleset.size/2 and pos2[1] == self.ruleset.size/2)):
            s1 = self.squares.get(x_coord=pos1[0], y_coord=pos1[1])
            s2 = self.squares.get(x_coord=pos2[0], y_coord=pos2[1])
            if(s1.member and not s2.member):
                if((s1.member.color == "BL" and not self.turn) or (s1.member.color == "WH" and self.turn)):
                    return True;
            else:
                print("Invalid 1")
        else:
            print("Invalid 2")
        return False;

    #checks in each direction if the move has resulted in a pawn capture
    def check_capture(self, pos1, pos2):
        #if not a king
        if (self.squares.get(x_coord=pos1[0], y_coord=pos1[1]).member.p_type == "KING"):
            return False #king can't capture

        #get own color
        mycolor = self.squares.get(x_coord=pos1[0], y_coord=pos1[1]).member.color

        #right neighbor square
        rs = self.squares.filter(x_coord=pos2[0], y_coord=pos2[1]+1)
        rs2 = self.squares.filter(x_coord=pos2[0], y_coord=pos2[1]+2)
        if (rs.exists() and rs2.exists()):
            self.check_capture_singledir(mycolor, rs, rs2)

        #left
        ls = self.squares.filter(x_coord=pos2[0], y_coord=pos2[1]-1)
        ls2 = self.squares.filter(x_coord=pos2[0], y_coord=pos2[1]-2)
        if (ls.exists() and ls2.exists()):
            self.check_capture_singledir(mycolor, ls, ls2)

        #down
        ds = self.squares.filter(x_coord=pos2[0]+1, y_coord=pos2[1])
        ds2 = self.squares.filter(x_coord=pos2[0]+2, y_coord=pos2[1])
        if (ds.exists() and ds2.exists()):
            self.check_capture_singledir(mycolor, ds, ds2)

        #up
        us = self.squares.filter(x_coord=pos2[0]-1, y_coord=pos2[1])
        us2 = self.squares.filter(x_coord=pos2[0]-2, y_coord=pos2[1])
        if (us.exists() and us2.exists()):
            self.check_capture_singledir(mycolor, us, us2)

    # checks if there's something capturable and does capture if so
    def check_capture_singledir(self, mycolor, s, s2):
        if s[0].member != None:
            if ((s[0].member.color != mycolor) and (s[0].member.p_type != "KING")): 
                #last part bc checking king capture in check_win
                if s2[0].member != None:
                    if ((s2[0].member.color == mycolor) and (s2[0].member.p_type != "KING")):
                        delS = self.squares.get(pk=s[0].pk)
                        delS.member = None
                        delS.save()

    def check_win(self, pos1, pos2):
        #if king, check his win conds, checking EDGE/CORNER
        #if black, check king capture
        return False

    # Moves the piece in pos1 to pos2
    def make_move(self, pos1, pos2):  
        s1 = self.squares.get(x_coord=pos1[0], y_coord=pos1[1])
        s2 = self.squares.get(x_coord=pos2[0], y_coord=pos2[1])
        s2.member = s1.member;
        s1.member = None;
        self.turn = not self.turn
        self.save()
        s1.save()
        s2.save()

    def players(self):
        return [self.black_player, self.white_player]

    # Given one player in the game, it will return the other player or 
    # None if there is no other player.
    def other_player(self, player):
        if(self.white_player == player):
            return self.black_player
        elif(self.black_player == player):
            return self.white_player
        else:
            return None

    def __unicode__(self):
        return str(self.timestamp)

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
    member = models.OneToOneField('Piece', blank=True, null=True)

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
