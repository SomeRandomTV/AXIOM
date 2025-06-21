# config.py
# This file loads some shit from .env

import os
from dotenv import load_dotenv

load_dotenv()

newsapi_key = os.getenv("NEWSAPI_KEY")
google_credentials = os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS", "CmdCraft/credentials.json")
whisper_model = os.getenv("WHISPER_MODEL")

print(newsapi_key)
print(google_credentials)
print(whisper_model)



