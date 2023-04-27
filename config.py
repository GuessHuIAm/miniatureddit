from secrets import token_hex

HOST = 'localhost'
PORT = 8000

# app.config related variables
SQLALCHEMY_DATABASE_URI = 'sqlite:///miniatureddit.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False # Silence the deprecation warning
SECRET_KEY = token_hex(16)