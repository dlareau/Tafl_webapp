from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage
from .models import *
import json

def send_move_update(player, move):
    redis_publisher = RedisPublisher(facility='game_move',
             users=[player.user.username])
    message = move
    message = RedisMessage(json.dumps(message))
    redis_publisher.publish_message(message)
