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

    def update_rank(self):
        self.rank = Game.objects.filter(winner=self).count()
        self.save()

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
    #============ End Player related game functions =============

    #============== Square related game functions ===============
    def get_square(self, pos):
        try:
            val = self.squares.get(x_coord=pos[0], y_coord=pos[1])
        except:
            val = None
        return val

    #returns an array of the four neighboring squares of the given pos
    def getNeighbors(self, pos):
        neighbors = []
        neighbors.append(self.squares.filter(x_coord=pos[0], y_coord=pos[1]-1))
        neighbors.append(self.squares.filter(x_coord=pos[0], y_coord=pos[1]+1))
        neighbors.append(self.squares.filter(x_coord=pos[0]-1, y_coord=pos[1]))
        neighbors.append(self.squares.filter(x_coord=pos[0]+1, y_coord=pos[1]))
        return neighbors
    #============ End Square related game functions =============

    #=========== Move/Capture related game functions ============
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
        return False

    # Returns true if the move is valid in the context of the current game
    def is_valid_move(self, pos1, pos2):
        if((not self.ruleset.valid_pos(pos1)) or (not self.ruleset.valid_pos(pos2))):
            return False
        if (self.is_move_clear(pos1, pos2) and not (self.ruleset.is_center(pos2) or self.ruleset.is_corner(pos2))):
            s1 = self.get_square(pos1)
            s2 = self.get_square(pos2)
            if(s1.member and not s2.member):
                if((s1.member.color == "BL" and not self.turn) or (s1.member.color == "WH" and self.turn)):
                    return True;
            else:
                print("Invalid 1")
        else:
            print("Invalid 2")
        return False;

    # checks in each direction if the move has resulted in a pawn capture
    def check_capture(self, pos1, pos2):
        #if not a king
        if (self.get_square(pos2).member.p_type == "KING"):
            return [] #king can't capture

        #need to send back to the frontend which squares to update
        toRemove = []

        up = self.check_capture_offset(pos2, (0,1))
        if(up): toRemove.append(up)
        down = self.check_capture_offset(pos2, (0,-1))
        if(down): toRemove.append(down)
        left = self.check_capture_offset(pos2, (-1,0))
        if(left): toRemove.append(left)
        right = self.check_capture_offset(pos2, (1,0))
        if(right): toRemove.append(right)
                
        return toRemove

    # Will check for a capture in a direction specified by and ofset. 
    def check_capture_offset(self, pos, offset):
        pos1 = self.get_square(pos)
        pos2 = self.get_square((pos[0]+offset[0], pos[1]+offset[1]))
        pos3 = self.get_square((pos[0]+2*offset[0], pos[1]+2*offset[1]))

        if((pos1 == None) or (pos1.member == None) or 
           (pos2 == None) or (pos2.member == None) or
           (pos3 == None) or (pos3.member == None)):
            return None

        mycolor = pos1.member.color

        if((pos1.member.p_type == "KING") or 
           (pos2.member.p_type == "KING") or 
           (pos3.member.p_type == "KING")):
            return None

        if((pos1.member.color != mycolor) or
           (pos2.member.color == mycolor) or
           (pos3.member.color != mycolor)):
            return None

        delS = self.squares.get(pk=pos2.pk)
        delS.member = None
        delS.save()
        return pos2

    def check_win(self):
        sq = self.squares.get(member__p_type = "KING")
        pos = (sq.x_coord, sq.y_coord)

        if (self.ruleset.win_cond == "EDGE" and self.ruleset.is_edge(pos)):
            return "W"
                # do end gamey things
        elif (self.ruleset.win_cond == "CORNER" and self.ruleset.is_corner(pos)):
            return "W"
                # do end gamey things

        #check if king surrounded by black
        kNeighbors = self.getNeighbors(pos)
        nCount = 0
        for kN in kNeighbors:
            if kN.exists() and kN[0].member != None and kN[0].member.color == "BL":
                nCount += 1
        if nCount == 4:
            return "B"
            #do end gamey things

        return "N"

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

    def __unicode__(self):
        return self.user.username + ": " + self.text[:20]
