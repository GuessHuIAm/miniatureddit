from gossip import GossipProtocol


class P2PNode:
    def __init__(self, self_ip, self_port, other_ip, other_port, session, context):
        self.gossip_protocol = GossipProtocol(self_ip, self_port, other_ip, other_port, session, context)

        print("P2PNode initialized, with peers: ", self.gossip_protocol.peers)

    def broadcast_user(self, user):
        command = f"INSERT INTO user (id, username, password_hash, date_created) VALUES \
                    ({user.id}, '{user.username}', '{user.password_hash}', '{user.date_created}');"
        self.gossip_protocol.broadcast(command)

    def broadcast_post(self, post):
        command = f"INSERT INTO post (id, title, content, upvotes, downvotes, author_id, anonymous, date_posted) VALUES \
                    ({post.id}, '{post.title}', '{post.content}', {post.upvotes}, {post.downvotes}, {post.author_id}, \
                    {post.anonymous}, '{post.date_posted}');"
        self.gossip_protocol.broadcast(command)

    def broadcast_comment(self, comment):
        command = f"INSERT INTO comment (id, post_id, author_id, content, anonymous, date_posted, upvotes, downvotes) VALUES \
                    ({comment.id}, {comment.post_id}, {comment.author_id}, '{comment.content}', \
                    {comment.anonymous}, '{comment.date_posted}', {comment.upvotes}, {comment.downvotes});"
        self.gossip_protocol.broadcast(command)

    def broadcast_vote(self, vote):
        command = f"REPLACE INTO vote (id, user_id, post_id, comment_id, is_upvote) VALUES \
                    ({vote.id}, {vote.user_id}, {vote.post_id}, \
                    {vote.comment_id}, {vote.is_upvote});"
        self.gossip_protocol.broadcast(command)

    def broadcast_delete_vote(self, vote):
        command = f"DELETE FROM vote WHERE id={vote.id};"
        self.gossip_protocol.broadcast(command)

    def broadcast_delete_post(self, post):
        command = f"UPDATE post SET deleted=1 WHERE id={post.id};"

