import os
from settings.base import *
from dotenv import load_dotenv

load_dotenv()

DEBUG = False

ALLOWED_HOSTS = []

SECRET_KEY = os.getenv("PROD_SECRET_KEY")
