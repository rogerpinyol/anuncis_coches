import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # MariaDB Config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MongoDB Config
    MONGO_URI = os.environ.get('MONGO_URI')
    MONGO_DB = os.environ.get('MONGO_DB')