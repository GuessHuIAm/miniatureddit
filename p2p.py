import socket
import threading
import json
from gossip import GossipProtocol


class P2PNode:
    def __init__(self, self_ip, self_port, other_ip='None', other_port='None'):
        self.gossip_protocol = GossipProtocol(self_ip, self_port)
        if not (other_ip == 'None' or other_port == 'None'):
            self.gossip_protocol.add_peer(other_ip, other_port)
            
        print("P2PNode initialized, with peers: ", self.gossip_protocol.peers)

    def broadcast_post(self, post):
        data = {
            'type': 'post',
            'content': post.content,
            'upvotes': post.upvotes,
            'downvotes': post.downvotes
        }
        self.gossip_protocol.broadcast(json.dumps(data))

    def broadcast_vote(self, type, post_id, is_upvote):
        data = {
            'type': 'vote',
            'post_type': type,
            'post_id': post_id,
            'is_upvote': is_upvote
        }
        self.gossip_protocol.broadcast(json.dumps(data))
