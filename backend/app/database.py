"""
database.py — async DB connection using databases + asyncpg
"""
import os
from databases import Database
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/killswitch")

database = Database(DATABASE_URL)
