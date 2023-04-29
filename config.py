from secrets import token_hex

HOST = 'localhost'
PORT = 8000

REP_1_HOST = HOST  # Default port number for replica 1
REP_1_PORT = 8001  # Default host address for replica 1
REP_2_HOST = HOST  # Default port number for replica 2
REP_2_PORT = 8002  # Default host address for replica 2

# app.config related variables
SQLALCHEMY_DATABASE_URI = 'sqlite:///miniatureddit.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False # Silence the deprecation warning
SECRET_KEY = token_hex(16)