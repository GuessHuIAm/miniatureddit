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
```
minatureddit/
├── README.md
├── app.py
├── commit_[IP ADDRESS].txt
├── config.py
├── forms.py
├── gossip.py
├── instance/
│   ├── miniatureddit.db
│   └── replica.db
├── models.py
├── notebook.md
├── p2p.py
├── p2psync_pb2.py
├── p2psync_pb2_grpc.py
├── protos
│   └── p2psync.proto
├── requirements.txt
├── static
│   ├── favicon.ico
│   ├── icon.png
│   └── main.css
└── templates
    ├── base.html
    ├── create_post.html
    ├── index.html
    ├── login.html
    ├── post.html
    ├── profile.html
    └── register.html
```
Here are the descriptions of a few relevant files:
- `forms.py`:
    In this file, we define the data models for our Flask application, which includes `User`, `Post`, `Comment`, and `Vote` classes. These classes are used to structure and manage the data related to users, posts, comments, and votes in our application. The file also initializes a SQLAlchemy instance (`db`) to handle database operations.
    - `User`: The `User` class represents a registered user in the system. It contains attributes such as `id`, `username`, `password_hash`, `posts`, `comments`, `date_created`, and `votes`. The class also includes methods to handle user authentication, password management, and user representation.
    - `Post`: The `Post` class represents a post created by a user. Attributes for this class include `id`, `title`, `content`, `author_id`, `anonymous`, `date_posted`, `deleted`, `comments`, and `votes`. The `Post` class also has methods to delete a post, get the number of upvotes, and get the number of downvotes.
    - `Comment`: The `Comment` class represents a comment made by a user on a post. It includes attributes such as `id`, `post_id`, `author_id`, `content`, `anonymous`, `parent_id`, `date_posted`, `deleted`, `votes`, and `children`. The `Comment` class has methods to delete a comment, check if a comment has a parent, and get the number of upvotes and downvotes.
    - `Vote`: The `Vote` class represents a user's vote on a post or a comment. It consists of attributes like `id`, `user_id`, `post_id`, `comment_id`, and is_upvote.

- `app.py`:
    This file provides the implementation of various routes and functionalities for a web application. Key features include:
    - Homepage Route: The `index()` function handles the homepage route. It displays all the posts in descending order of their posting date. Additionally, it allows users to search for posts by providing a query.
    - User Authentication: The file includes user authentication with login and registration functionality. It handles form submission and validation, password hashing, and user session management.
    - User Profile: Users can view their profile or other user's profiles, which includes the posts authored by them. The profile route checks whether the current user is viewing their own profile or another user's profile.
    - Post and Comment Creation: The file provides routes and functions for creating new posts and comments. Users can create content only if they are logged in. The content can be posted anonymously or by using the user's identity.
    - Content Deletion: Users can delete their own posts and comments. Deletion is restricted to the content author only.
    - Upvoting Posts and Comments: The file includes a route for upvoting posts and comments.

- `gossip.py`:
    This file implements the `GossipProtocol` class, which is responsible for facilitating P2P communication and synchronization between nodes in the network. The class is initialized with the IP addresses and ports of the current node and another node, as well as the database session and application context.

    Key components of the `GossipProtocol` class include:
    Initialization: The class sets up a list of peers and initializes a commit log file for the current node. It also loads commits from other peers and updates the database accordingly.
    - `load_commits()`: This method iterates through the list of peers and tries to receive commit logs from them. If new logs are found, it updates the database and breaks the loop. If no updates are found, it raises an exception.
    - `receive_commit_log()`: This method receives commit logs from a given peer, filters the logs based on the `commit_counter`, and returns the new_logs list.
    - `update_database()`: This method updates the database with the new_logs list, executing the commits and updating the commit log file.
    - `broadcast()`: This method broadcasts a command to all peers in the network and updates the commit log. It increments the `commit_counter` and sends the command to all peers using the SendCommand RPC.
    - `stop()`: This method sets the `stop_flag` to True, indicating that the `GossipProtocol` should stop running.

    Additionally, the file imports necessary libraries and modules, and sets global variables to handle database sessions, application context, commit log files, and commit counters.

- gRPC:
    Internode communication was implemented using gRPC, and the server capabilities of each node are summarized by the following RPCs and Messages:
    ```
    service P2PSync{
        rpc PeerListUpdate(Empty) returns (PeerUpdate) {}
        rpc ListenCommands(Empty) returns (stream DatabaseCommand) {}
        rpc Connect(Peer) returns (Empty) {}
        rpc Heartbeat(Empty) returns (Empty) {}
        rpc SendCommand(DatabaseCommand) returns (Empty) {}
        rpc RequestPeerList(Peer) returns (PeerList) {}
    }

    message Empty {
    }

    message PeerUpdate {
        Peer peer = 1;
        bool add = 2;
    }

    message PeerList {
        repeated Peer peers = 1;
    }

    message Peer {
        string host = 1;
        string port = 2;
    }

    message DatabaseCommand {
        int32 timestamp = 1;
        string command = 2;
    }
    ```

    - `PeerListUpdate` allows a client signify a change to the peer list (the list of connected nodes in the network), providing that other `Peer` nodes should add or delete from their peer list (whether they should add or delete the node is specified by the boolean flag add in the message type `PeerUpdate`). This keeps all the nodes in the network aware of the state of the network at all times.
    - `ListenCommands` allows the new node to request for the commit log of the node that it has connected to, receiving it as a stream of `DatabaseCommands`, which we use at start up, in conjunction with logic implemented in `gossip.py` and `p2p.py`.
    - `Connect` allows a new node to connect to an existing one, in which the existing one adds the new node to its own peer list, broadcasts this change to each of its other peers, and then starts a continuous heartbeat with the new node.
    - `Heartbeat` effectively just allows nodes to ping each other, sending empty messages back and forth.
    - `SendCommand` allows nodes to broadcast a SQL database command to another node.
    - `RequestPeerList` allows nodes to request for the most up-to-date peer list of another node.
