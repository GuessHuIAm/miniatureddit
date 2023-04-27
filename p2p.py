import socket
import threading
import json
from gossip import GossipProtocol


class P2PNode:
    def __init__(self):
        self.gossip_protocol = GossipProtocol()
        self.peers = []

    def broadcast_post(self, post):
        data = {
            'type': 'post',
            'content': post.content,
            'upvotes': post.upvotes,
            'downvotes': post.downvotes
        }
        self.gossip_protocol.broadcast(json.dumps(data))

    def broadcast_vote(self, post_id, is_upvote):
        data = {
            'type': 'vote',
            'post_id': post_id,
            'is_upvote': is_upvote
        }
        self.gossip_protocol.broadcast(json.dumps(data))
