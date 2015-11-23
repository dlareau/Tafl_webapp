from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage
from .models import *
import json

def send_move_update(player, move):
    redis_publisher = RedisPublisher(facility='game_move',
             users=[player.user.username])
    message = {}
    message['move'] = move
    message['capture'] = False
    message = RedisMessage(json.dumps(message))
    redis_publisher.publish_message(message)

def send_capture(player1, player2, pos):
    redis_publisher = RedisPublisher(facility='game_move',
             users=[player1.user.username, player2.user.username])
    message = {}
    message['capture'] = True
    message['pos'] = pos
    message = RedisMessage(json.dumps(message))
    redis_publisher.publish_message(message)

def send_win(player1, player2):
    redis_publisher = RedisPublisher(facility='game_move',
             users=[player1.user.username, player2.user.username])
    message = {}
    message['win'] = True
    message = RedisMessage(json.dumps(message))
    redis_publisher.publish_message(message)

def send_message(player1, player2, msg):
    redis_publisher = RedisPublisher(facility='chat',
             users=[player1.user.username, player2.user.username])
    message = {}
    message['name'] = msg.user.username
    message['text'] = msg.text
    message['time'] = str(msg.time)
    message = RedisMessage(json.dumps(message))
    redis_publisher.publish_message(message)

def send_join(player, new_player):
    redis_publisher = RedisPublisher(facility='game_join',
             users=[player.user.username])
    message = new_player.user.username
    message = RedisMessage(json.dumps(message))
    redis_publisher.publish_message(message)