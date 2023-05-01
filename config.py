from secrets import token_hex

HOST = 'localhost'
PORT = 8000

REP_1_HOST = HOST  # Default port number for replica 1
REP_1_PORT = 8001  # Default host address for replica 1
REP_2_HOST = HOST  # Default port number for replica 2
REP_2_PORT = 8002  # Default host address for replica 2

# app.config related variables
AUTO_READ_ON_SLAVE = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///miniatureddit.db'
SQLALCHEMY_DATABASE_REPLICA_URI = 'sqlite:///replica.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False # Silence the deprecation warning
SQLALCHEMY_BINDS = {
    'master': SQLALCHEMY_DATABASE_URI,
    'slave': SQLALCHEMY_DATABASE_REPLICA_URI
}

SECRET_KEY = token_hex(16)