By Jonathan Luo, Michael Hu, and Matt Kiley

There are few HTML pages:
- index.html: Landing page and also where the main post board will be displayed (TBD filtering post by people, communities, controversial, etc.).
The posts here will show author, content, net like/dislike (no actual like/dislike ratio), the number of comments (not the comments themselves), and an option to like/dislike.
- post.html: A page for an individual post, showing author, content, like/dislike ratio, the comments themselves (option to like/dislike comments), option to like/dislike, and an option to leave a comment.
- create.html: Where one would create a post. Give content and an option to turn this anonymous.
- profile.html: Show this user's individual profile: username,
their posts, and their latest comments. Option to delete and change password.
- login.html: Login into an existing account. Needed for any type of interactions
aside from just viewing posts from index.html.
- register.html: Create an account.

This is a text-sharing platform like Reddit implemented in a peer-to-peer fashion, broadcasted using a gossip protocol

Before login, the app must first register the current IP address that the program is running it,
and it will then ask for at least one other user's IP address in the network so that the current user can join the peer-to-peer network (unless this is the only node currently out there). We
use this other IP address to exchange handshake with another node in the network and if possible,
replicate the database of the other node.


Once the user is logged in, they can create posts, comment on existing posts, and vote on posts and comments. The gossip protocol will be used to propagate new posts and votes across the network.