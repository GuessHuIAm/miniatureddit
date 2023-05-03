# Design Notebook for MiniatuReddit
By Jonathan Luo, Michael Hu, and Matt Kiley

This is a text-sharing platform like Reddit implemented in a peer-to-peer fashion.

## Action Flow
Before the Flask app even starts, the app must first register the current IP address that the program is running on, and it will then ask for at least one other user's IP address in the network so that the current user can join the P2P network (unless this is the only node currently out there, then we just start a new network). We use this other IP address to exchange handshake with another node in the network.
The handshake consists of the following (done through gRPC):
- Verification that the node at the IP address is alive (a connection is formed).
- The new node receives from the existing node a list of the peers on the network.
- The existing node streams its commit log to the new node so that the database is up to date.

The commit log is a CSV file in the format of TIMESTAMP|SQL_COMMAND.

If the handshake is unsuccessful, then we ask again for an IP address.

Once the user is logged in, they can create posts, comment on existing posts, and vote on posts and comments. The gossip protocol will be used to propagate new posts and votes across the network.


## Architecture
There are few HTML pages:
- index.html: This is the landing page and where the main post board will be displayed.
The posts here will show author, content, the like to dislike ratio, the number of comments (not the comments themselves), and an option to like/dislike.
- post.html: A page for an individual post, showing author, content, like/dislike ratio, the comments themselves (option to like/dislike comments), option to like/dislike, and an option to leave a comment.
- create.html: Where one would create a post. The user will need to give some content and then choose if they want 
it to be anonymous or not.
- profile.html: Show this user's individual profile: username,
their posts, and their latest comments. Option to delete and change password.
- login.html: Login into an existing account. Needed for any type of interactions
aside from just viewing posts from the landing page.
- register.html: Create an account.