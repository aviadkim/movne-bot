from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, date
from typing import List, Dict, Optional
import os
import sys
from pydantic import BaseModel

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from src.database.models import DatabaseManager

router = APIRouter(prefix="/conversations", tags=["conversations"])

class ConversationFilter(BaseModel):
    leads_only: bool = False
    date: Optional[date] = None

class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class Conversation(BaseModel):
    conversation_id: str
    start_time: str
    contact: Optional[str] = None
    investor_status: Optional[str] = None
    lead_captured: Optional[bool] = None
    messages: List[Message]

class ConversationViewer:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_filtered_conversations(self, filter_leads: bool = False, filter_date: Optional[date] = None) -> List[Dict]:
        """Get filtered conversations from database"""
        try:
            conversations = self.db_manager.get_all_conversations()
            
            if not conversations:
                return []

            filtered_conversations = []
            for conv in conversations:
                try:
                    # Apply lead filter
                    if filter_leads and not conv.get('lead_captured'):
                        continue
                    
                    # Apply date filter
                    start_time = conv.get('start_time', '')
                    if not start_time:
                        continue

                    try:
                        conv_date = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S.%f').date()
                    except:
                        continue

                    if filter_date and conv_date != filter_date:
                        continue
                    
                    # Format messages
                    messages = conv.get('messages', [])
                    formatted_messages = []
                    for msg in messages:
                        if msg.get('role') and msg.get('content'):
                            formatted_messages.append({
                                'role': msg['role'],
                                'content': msg['content'],
                                'timestamp': msg.get('timestamp')
                            })
                    
                    # Format conversation
                    formatted_conv = {
                        'conversation_id': conv.get('conversation_id'),
                        'start_time': start_time,
                        'contact': conv.get('contact'),
                        'investor_status': conv.get('investor_status'),
                        'lead_captured': conv.get('lead_captured'),
                        'messages': formatted_messages
                    }
                    
                    filtered_conversations.append(formatted_conv)

                except Exception as e:
                    continue  # Skip conversations with errors

            return filtered_conversations

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")

# FastAPI endpoints
@router.get("/", response_model=List[Conversation])
async def get_conversations(
    leads_only: bool = Query(False, description="Filter to show only leads"),
    filter_date: Optional[date] = Query(None, description="Filter by specific date")
):
    """Get filtered conversations"""
    try:
        db = DatabaseManager()
        viewer = ConversationViewer(db)
        return viewer.get_filtered_conversations(leads_only, filter_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation by ID"""
    try:
        db = DatabaseManager()
        viewer = ConversationViewer(db)
        conversations = viewer.get_filtered_conversations()
        
        for conv in conversations:
            if conv['conversation_id'] == conversation_id:
                return conv
                
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
