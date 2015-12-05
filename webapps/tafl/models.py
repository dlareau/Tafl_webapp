from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from math import exp
from tafl.redis import *

now = timezone.now()

class Player(models.Model):
    user = models.ForeignKey(User)
    cur_game = models.ForeignKey('Game', blank=True, null=True)
    rank = models.IntegerField(default=0)

    def __unicode__(self):
        return self.user.username

    def update_rank(self, new_rank):
        self.rank = new_rank
        self.save()

    def num_games(self):
        return (Game.objects.filter(black_player=self).count() + 
                Game.objects.filter(white_player=self).count())

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
    is_priv = models.BooleanField(default=False)
    priv_pw = models.CharField(max_length=200, blank=True, null=True)

    #============== Player related game functions ===============
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

    # Updates the ranks, does nothing if game is not yet finished.
    def update_ranks(self):
        if(self.winner == None):
            return
        point_diff = self.black_player.rank - self.white_player.rank

        # Calculates and updates the ELO rating for white
        wg_factor = y=20.0*exp(-0.05 * self.white_player.num_games())+10
        white_win = 1.0 if self.white_player == self.winner else 0.0
        e_white = (1.0 / (1.0 + pow(10, (point_diff / 400)))) 
        white_new = (self.white_player.rank + wg_factor * (white_win - e_white))
        self.white_player.update_rank(white_new)

        # Calculates and updates the ELO rating for black
        bg_factor = y=20.0*exp(-0.05 * self.black_player.num_games())+10
        black_win = 1.0 - white_win
        e_black = 1.0 - e_white
        black_new = (self.black_player.rank + bg_factor * (black_win - e_black))
        self.black_player.update_rank(black_new)
        
    #============ End Player related game functions =============

    #============== Square related game functions ===============
    # Given a position it returns a square or None if the square doesn't exist
    def get_square(self, pos):
        try:
            val = self.squares.get(x_coord=pos[0], y_coord=pos[1])
        except:
            val = None
        return val

    # Returns an array of the four neighboring squares of the given pos
    def getNeighbors(self, pos):
        neighbors = []
        neighbors.append(self.squares.filter(x_coord=pos[0], y_coord=pos[1]-1))
        neighbors.append(self.squares.filter(x_coord=pos[0], y_coord=pos[1]+1))
        neighbors.append(self.squares.filter(x_coord=pos[0]-1, y_coord=pos[1]))
        neighbors.append(self.squares.filter(x_coord=pos[0]+1, y_coord=pos[1]))
        return neighbors
    #============ End Square related game functions =============

    #=========== Move/Capture related game functions ============
    # Returns True if there are no pieces between pos1 and pos2 (exclusive)
    # Will also return False if the two peices are not in the same row or col
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
        return False

    # Returns true if the move is valid in the context of the current game
    def is_valid_move(self, pos1, pos2):
        # Make sure both positions are valid game locations
        if((not self.ruleset.valid_pos(pos1)) or (not self.ruleset.valid_pos(pos2))):
            return False
        # Check for pieces in the way, the throne and corners
        if (self.is_move_clear(pos1, pos2) and not (self.ruleset.is_center(pos2) or self.ruleset.is_corner(pos2))):
            s1 = self.get_square(pos1)
            s2 = self.get_square(pos2)
            # Make sure there is actually a piece to move and the dest is empty
            if(s1.member and not s2.member):
                if((s1.member.color == "BL" and not self.turn) or (s1.member.color == "WH" and self.turn)):
                    return True;
            else:
                print("Invalid 1")
        else:
            print("Invalid 2")
        return False;

    # Checks in each direction if the move has resulted in a pawn capture
    # Pos should be the piece just moved that would incite capture.
    def check_capture(self, pos):
        # Make sure we aren't a king, because king's can't capture.
        if (self.get_square(pos).member.p_type == "KING"):
            return [] #king can't capture

        # Need to send back to the frontend which squares to update
        toRemove = []

        # Check orthogonal directions for capture.
        up = self.capture_offset(pos, (0,1))
        if(up): toRemove.append(up)
        down = self.capture_offset(pos, (0,-1))
        if(down): toRemove.append(down)
        left = self.capture_offset(pos, (-1,0))
        if(left): toRemove.append(left)
        right = self.capture_offset(pos, (1,0))
        if(right): toRemove.append(right)
                
        return toRemove

    # Will check for a capture in a direction specified by an ofset. 
    def capture_offset(self, pos, offset):
        pos1 = self.get_square(pos)
        pos2 = self.get_square((pos[0]+offset[0], pos[1]+offset[1]))
        pos3 = self.get_square((pos[0]+2*offset[0], pos[1]+2*offset[1]))

        # Are all the squares legal and populated?
        if((pos1 == None) or (pos1.member == None) or 
           (pos2 == None) or (pos2.member == None) or
           (pos3 == None) or (pos3.member == None)):
            return None

        mycolor = pos1.member.color

        # Kings can not be involved in capture
        if((pos1.member.p_type == "KING") or 
           (pos2.member.p_type == "KING") or 
           (pos3.member.p_type == "KING")):
            return None

        # Check for proper color pattern
        if((pos1.member.color != mycolor) or
           (pos2.member.color == mycolor) or
           (pos3.member.color != mycolor)):
            return None

        # Capture piece and return which piece to delete clientside
        delS = self.squares.get(pk=pos2.pk)
        delS.member = None
        delS.save()
        return pos2

    # Moves the piece in pos1 to pos2
    def make_move(self, pos1, pos2):  
        s1 = self.get_square(pos1)
        s2 = self.get_square(pos2)
        s2.member = s1.member;
        s1.member = None;
        self.turn = not self.turn
        self.save()
        s1.save()
        s2.save()

    #========= End Move/Capture related game functions ==========

    #=========== Win/Endgame related game functions =============
    # Checks to see if the current board state is considered winning
    # Returns the winning player object or None if nobody has won
    def check_win(self):
        sq = self.squares.get(member__p_type = "KING")
        pos = (sq.x_coord, sq.y_coord)

        # Check for white victory in an edge-escape game
        if (self.ruleset.win_cond == "EDGE" and self.ruleset.is_edge(pos)):
            return self.white_player

        # Check for white victory in a corner-escape game
        elif (self.ruleset.win_cond == "CORNER" and self.ruleset.is_corner(pos)):
            return self.white_player

        # Check if king surrounded by black
        kNeighbors = self.getNeighbors(pos)
        nCount = 0
        for kN in kNeighbors:
            if kN.exists() and kN[0].member != None and kN[0].member.color == "BL":
                nCount += 1
        if nCount == 4:
            return self.black_player

        return None

    def end_game(self, winner):
        self.winner = winner
        self.update_ranks();
        self.save()
        self.black_player.cur_game = None
        self.black_player.save()
        self.white_player.cur_game = None
        self.white_player.save()
        send_win(winner, self.other_player(winner))
    #========= End Win/Endgame related game functions ===========

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

    # These are techinically more related to squares, but they rely on the 
    # current ruleset, so they live here.
    def is_corner(self, pos):
        return ((pos[0] == 0 or pos[0] == self.size-1) and 
                (pos[1] == 0 or pos[1] == self.size-1))

    def is_edge(self, pos):
        return ((pos[0] == 0 or pos[0] == self.size-1) or 
                (pos[1] == 0 or pos[1] == self.size-1))

    def valid_pos(self, pos):
        row_valid = (0 <= pos[0] and pos[0] < self.size)
        col_valid = (0 <= pos[1] and pos[1] < self.size)
        return row_valid and col_valid

    def is_center(self, pos):
        return (pos[0] == self.size/2 and pos[1] == self.size/2)

class ChatMessage(models.Model):
    user = models.ForeignKey(User)
    text = models.CharField(max_length=400)
    time = models.DateTimeField()
    game = models.ForeignKey(Game)

    def __unicode__(self):
        return self.user.username + ": " + self.text[:20]
