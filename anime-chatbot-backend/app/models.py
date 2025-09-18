import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from app.db import messages_collection

load_dotenv()

# LLM setup
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7,
)

def load_memory(user_id: str):
    """Reconstruct memory from MongoDB chat history."""
    past_messages = messages_collection.find({"user_id": user_id}).sort("_id", 1)

    # Build memory object
    memory = ConversationBufferMemory(return_messages=True)
    for msg in past_messages:
        if msg["sender"] == "user":
            memory.chat_memory.add_message(HumanMessage(content=msg["text"]))
        else:
            memory.chat_memory.add_message(AIMessage(content=msg["text"]))
    return memory

def generate_reply(user_id: str, user_message: str) -> str:
    """Generate reply with persistent memory (per user)."""
    try:
        # Load memory for this user
        memory = load_memory(user_id)

        # Create conversation chain with memory
        conversation = ConversationChain(
            llm=llm,
            memory=memory,
            verbose=True,
        )

        # Get response
        response = conversation.invoke({"input": user_message})
        bot_reply = response["response"]

        # Save to DB
        messages_collection.insert_one({"user_id": user_id, "sender": "user", "text": user_message})
        messages_collection.insert_one({"user_id": user_id, "sender": "bot", "text": bot_reply})

        return bot_reply
    except Exception as e:
        print("Error:", e)
        return "⚠️ Gemini API error"
