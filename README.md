# MiniatuReddit

MinatuReddit is a text-sharing platform like Reddit implemented in a peer-to-peer fashion. Users can perform a number of operations, namely:
- Register a new account
- Log into a registered account
- Post posts
- Comment on posts
- Reply to comments
- Upvote and downvote both posts and comments alike
- Delete posts and comments
- Search for specific posts
- View one’s own profile, as well as those of other users (profiles show what posts a user has made)
- Logout

## Getting Started
To make sure you have all the required modules for this application, run `pip install -r requirements.txt` before continuing!

To use the application, run `python app.py [port number=5000]` or `flask run`. The port number parameter is to change which port number the Flask application (our node itself has a port number and the user interface has another one) will be deployed on, and sometimes, especially while testing on one device, one might want to use multiple ports.
Once started, the application will prompt you to enter an IP address and port number. If you are the origin node for the network (i.e. there are no other nodes in the network), you need to enter “None” when prompted for the IP address and any key for the port number to begin the network. To connect to an existing network, you just need to enter the IP address and port number of another node in the network, and our program will do the rest for you. If at any time all nodes are disconnected, to revive the system to its latest state, it is necessary to kickstart the latest node that died.

