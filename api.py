from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, constr
from src.bot.context import BotContext
from src.database.models import DatabaseManager
from src.dashboard.analytics import router as analytics_router
from src.utils.lead_tracker import router as leads_router
from src.utils.conversation_viewer import router as conversations_router
import uvicorn
import os
from dotenv import load_dotenv
import uuid
import logging
from typing import Optional
from fastapi.security import APIKeyHeader
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
PORT = int(os.getenv("PORT", 8080))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY environment variable is required")

app = FastAPI(
    title="Movne Bot API",
    description="API for Movne Bot chat interactions, analytics, and lead management",
    version="1.0.0"
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Initialize components
db_manager = DatabaseManager()
bot_context = BotContext()

# Models
class ChatRequest(BaseModel):
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=4000, 
        description="User message"
    )
    conversation_id: Optional[str] = Field(None, description="Unique conversation identifier")

class ChatResponse(BaseModel):
    response: str
    conversation_id: str

class ErrorResponse(BaseModel):
    detail: str

# Security
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

# Include routers
app.include_router(
    analytics_router,
    prefix="/api",
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    leads_router,
    prefix="/api",
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    conversations_router,
    prefix="/api",
    dependencies=[Depends(verify_api_key)]
)

# Routes
@app.post("/api/chat", 
         response_model=ChatResponse,
         responses={
             400: {"model": ErrorResponse},
             500: {"model": ErrorResponse}
         })
async def chat_endpoint(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Process a chat message and return the bot's response.
    
    - If no conversation_id is provided, a new one will be created
    - Messages are saved to the database for context and analytics
    """
    try:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        logger.info(f"Processing chat request - Conversation ID: {conversation_id}")
        
        # Ensure conversation exists
        db_manager.create_conversation_if_not_exists(conversation_id)
        
        # Get bot response
        response = bot_context.get_response(
            request.message,
            db_manager,
            conversation_id
        )
        
        logger.info(f"Successfully processed chat request - Conversation ID: {conversation_id}")
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id
        )
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {str(e)}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred. Please try again later."
        )

@app.get("/health")
async def health_check(api_key: str = Depends(verify_api_key)):
    """
    Check the health status of the API and its dependencies.
    
    Verifies:
    - Database connection
    - Anthropic API connection
    """
    try:
        # Test database connection
        test_conversation_id = str(uuid.uuid4())
        db_manager.create_conversation_if_not_exists(test_conversation_id)
        
        # Test Anthropic API
        response = bot_context.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )
        
        return {
            "status": "healthy",
            "database": "connected",
            "anthropic_api": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )

# Serve static files for forms
app.mount("/forms", StaticFiles(directory="forms"), name="forms")

@app.get("/")
async def root():
    """Redirect to API documentation"""
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Movne Bot API Documentation")

if __name__ == "__main__":
    logger.info(f"Starting server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
