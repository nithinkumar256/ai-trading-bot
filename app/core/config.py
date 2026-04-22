from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    def __init__(self):
        self.APP_NAME = os.getenv("APP_NAME", "AI Trading Bot")
        self.DEBUG = os.getenv("DEBUG", "False") == "True"
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 👇 THIS LINE IS CRITICAL
settings = Settings()