import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MariaDB Config
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://username:password@localhost/car_marketplace')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MongoDB Config
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB = os.getenv('MONGO_DB', 'car_marketplace')