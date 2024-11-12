import sqlite3
import logging
import sys
from datetime import datetime, timezone
import uuid
import os

class DatabaseManager:
    def __init__(self):
        # Use absolute path for database
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_dir = os.path.join(self.base_dir, 'database')
        self.db_path = os.path.join(self.db_dir, 'movne_chat.db')
        
        # Setup logging for Heroku
        self.setup_logging()
        
        # Ensure database directory exists
        os.makedirs(self.db_dir, exist_ok=True)
        
        self.init_db()

    def setup_logging(self):
        """Set up logging configuration for Heroku"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            # Create tables with correct schema
            c.execute('''CREATE TABLE IF NOT EXISTS conversations
                     (conversation_id TEXT PRIMARY KEY,
                      start_time TIMESTAMP,
                      end_time TIMESTAMP,
                      success_score FLOAT,
                      lead_captured BOOLEAN,
                      investor_status TEXT,
                      qualification_reason TEXT)''')

            c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (message_id TEXT PRIMARY KEY,
                      conversation_id TEXT,
                      timestamp TIMESTAMP,
                      role TEXT,
                      content TEXT,
                      FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id))''')

            c.execute('''CREATE TABLE IF NOT EXISTS leads
                     (lead_id TEXT PRIMARY KEY,
                      conversation_id TEXT,
                      contact_type TEXT,
                      contact_value TEXT,
                      timestamp TIMESTAMP,
                      status TEXT,
                      notes TEXT,
                      investor_status TEXT,
                      agreement_status TEXT,
                      FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id))''')

            conn.commit()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            raise
        finally:
            conn.close()

    def get_all_conversations(self, limit: int = None, offset: int = 0) -> list:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            query = '''
                SELECT 
                    c.conversation_id,
                    c.start_time,
                    c.lead_captured,
                    c.investor_status,
                    m.timestamp,
                    m.role,
                    m.content,
                    l.contact_value
                FROM conversations c
                LEFT JOIN messages m ON c.conversation_id = m.conversation_id
                LEFT JOIN leads l ON c.conversation_id = l.conversation_id
                ORDER BY c.start_time DESC, m.timestamp ASC
            '''
            
            if limit:
                query += f' LIMIT {limit} OFFSET {offset}'
            
            c.execute(query)
            rows = c.fetchall()
            
            conversations = {}
            for row in rows:
                conv_id = row[0]
                if conv_id not in conversations:
                    conversations[conv_id] = {
                        'conversation_id': conv_id,
                        'start_time': row[1],
                        'lead_captured': row[2],
                        'investor_status': row[3],
                        'contact': row[7],
                        'messages': []
                    }
                if row[5] and row[6]:
                    conversations[conv_id]['messages'].append({
                        'timestamp': row[4],
                        'role': row[5],
                        'content': row[6]
                    })
            
            return list(conversations.values())
            
        except Exception as e:
            self.logger.error(f"Failed to get conversations: {str(e)}")
            return []
        finally:
            conn.close()

    def get_conversation_history(self, conversation_id: str, limit: int = None) -> list:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            query = '''SELECT role, content FROM messages 
                      WHERE conversation_id = ? 
                      ORDER BY timestamp ASC'''
            
            if limit:
                query += f' LIMIT {limit}'
                
            c.execute(query, (conversation_id,))
            messages = c.fetchall()
            return messages
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation history: {str(e)}")
            return []
        finally:
            conn.close()

    def save_message(self, conversation_id: str, role: str, content: str):
        try:
            self.create_conversation_if_not_exists(conversation_id)
            
            conn = self.get_connection()
            c = conn.cursor()
            c.execute('''INSERT INTO messages (message_id, conversation_id, timestamp, role, content)
                        VALUES (?, ?, ?, ?, ?)''',
                     (str(uuid.uuid4()), conversation_id, datetime.now(), role, content))
            conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save message: {str(e)}")
        finally:
            conn.close()

    def create_conversation_if_not_exists(self, conversation_id: str):
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            c.execute('SELECT 1 FROM conversations WHERE conversation_id = ?', (conversation_id,))
            if not c.fetchone():
                c.execute('''INSERT INTO conversations 
                            (conversation_id, start_time, lead_captured)
                            VALUES (?, ?, ?)''',
                         (conversation_id, datetime.now(), False))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to create conversation: {str(e)}")
        finally:
            conn.close()

    def save_lead(self, conversation_id: str, contact_type: str, contact_value: str, notes: str = None):
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            lead_id = str(uuid.uuid4())
            c.execute('''INSERT INTO leads 
                        (lead_id, conversation_id, contact_type, contact_value, timestamp, 
                         status, notes, investor_status, agreement_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (lead_id, conversation_id, contact_type, contact_value, 
                      datetime.now(), 'new', notes, None, None))
            
            c.execute('''UPDATE conversations 
                        SET lead_captured = ? 
                        WHERE conversation_id = ?''',
                     (True, conversation_id))
            
            conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save lead: {str(e)}")
        finally:
            conn.close()
