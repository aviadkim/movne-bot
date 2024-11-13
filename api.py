from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.bot.context import BotContext
from src.database.models import DatabaseManager
import uvicorn
import os
from dotenv import load_dotenv
import uuid
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

app = FastAPI(title="Movne Bot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize components
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
        
        # Log incoming request
        logging.info(f"Received message: {request.message[:50]}...")
        
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
        logging.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        # Test database connection
        db_manager.create_conversation_if_not_exists(str(uuid.uuid4()))
        
        # Test Anthropic API
        bot_context.client.messages.create(
            messages=[{"role": "user", "content": "test"}],
            model="claude-3-opus-20240229",
            max_tokens=10
        )
        
        return {
            "status": "healthy",
            "database": "connected",
            "anthropic_api": "connected"
        }
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
