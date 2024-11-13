from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.bot.context import BotContext
from src.database.models import DatabaseManager
import uvicorn
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

app = FastAPI()
db_manager = DatabaseManager()
bot_context = BotContext()

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Ensure conversation exists
        db_manager.create_conversation_if_not_exists(conversation_id)
        
        # Get bot response
        response = bot_context.get_response(
            request.message,
            db_manager,
            conversation_id
        )
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
