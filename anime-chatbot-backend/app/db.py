from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "your_mongo_connection_string")

try:
    client = MongoClient(MONGO_URI)
    client.admin.command("ping")  # check connection
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

# Database + collection
db = client["anime_chatbot"]
messages_collection = db["messages"]
