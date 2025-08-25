# config.py
# This file loads some shit from .env

import os
from dotenv import load_dotenv
#Something
load_dotenv()

newsapi_key = os.getenv("NEWS_API_KEY")
google_credentials = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "../../secrets/credentials.json")
whisper_model = os.getenv("WHISPER_MODEL")


with open(google_credentials, "r") as f:
    print(f.read())



