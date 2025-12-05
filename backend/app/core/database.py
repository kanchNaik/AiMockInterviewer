# from motor.motor_asyncio import AsyncIOMotorClient
# from pymongo import ASCENDING, DESCENDING

# # keep your connection string; fill the password if needed
# # MONGO_URL = "mongodb+srv://priyagovindarajulu_db_user:YOUR_PASSWORD@cluster0.prvspza.mongodb.net/?appName=Cluster0"
# MONGO_URL = "mongodb+srv://priyagovindarajulu_db_user:@cluster0.prvspza.mongodb.net/?appName=Cluster0"
# DB_NAME = "ai_mock_interviewer"

# client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
# db = client[DB_NAME]

# async def ensure_indexes():
#     # users: unique email
#     await db["users"].create_index([("email", ASCENDING)], unique=True, name="users_email_uq")

#     # sessions: allow both userId and legacy userEmail filtering
#     await db["sessions"].create_index([("sessionId", ASCENDING)], unique=True, name="sessions_sessionId_uq")
#     await db["sessions"].create_index([("userId", ASCENDING), ("createdAt", DESCENDING)],
#                                       name="sessions_userId_created_idx")
#     await db["sessions"].create_index([("userEmail", ASCENDING), ("createdAt", DESCENDING)],
#                                       name="sessions_userEmail_created_idx")

#     # turns: one doc per (sessionId, index)
#     await db["turns"].create_index([("sessionId", ASCENDING), ("index", ASCENDING)],
#                                    unique=True, name="turns_session_index_uq")

# async def ping():
#     await ensure_indexes()
#     return await db.command("ping")

from dotenv import load_dotenv
load_dotenv()

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING

# keep your connection string; fill the password if needed
MONGO_URL = os.getenv("MONGO_URL", "")
DB_NAME = "ai_mock_interviewer"

client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

async def ensure_indexes():
    # users: unique email
    await db["users"].create_index([("email", ASCENDING)], unique=True, name="users_email_uq")

    # sessions indexes
    await db["sessions"].create_index([("sessionId", ASCENDING)], unique=True, name="sessions_sessionId_uq")
    await db["sessions"].create_index([("userId", ASCENDING), ("createdAt", DESCENDING)],
                                      name="sessions_userId_created_idx")
    await db["sessions"].create_index([("userEmail", ASCENDING), ("createdAt", DESCENDING)],
                                      name="sessions_userEmail_created_idx")

    # turns indexes
    await db["turns"].create_index([("sessionId", ASCENDING), ("index", ASCENDING)],
                                   unique=True, name="turns_session_index_uq")

async def ping():
    await ensure_indexes()
    return await db.command("ping")
