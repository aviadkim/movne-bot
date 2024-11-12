import json
from pathlib import Path
import logging
import sys
from datetime import datetime
import os
import sqlite3
import pandas as pd
from typing import Dict, List, Optional, Union
import re
from collections import defaultdict

class DocumentProcessor:
    def __init__(self):
        self.knowledge_base = {
            "company": """
            מובנה גלובל הינה חברה לשיווק השקעות בעלת רישיון מרשות ניירות ערך.
            החברה מתמחה במוצרים פיננסיים מובנים ופועלת בשקיפות מלאה מול לקוחותיה.
            אנו מספקים פתרונות השקעה מותאמים אישית למשקיעים כשירים.
            """,
            
            "product": """
            המוצרים שלנו הם מכשירים פיננסיים מובנים המונפקים על ידי בנקים בינלאומיים מובילים.
            המוצרים מאפשרים חשיפה לשווקים הפיננסיים עם הגנות מובנות.
            כל מוצר מותאם לצרכי הלקוח ומאפשר נזילות יומית.
            """,
            
            "advantages": """
            1. נזילות יומית עם מחיר מהמנפיק
            2. העסקה ישירה מול הבנק ללא צד שלישי
            3. המוצר נמצא בחשבון הבנק של הלקוח
            4. שקיפות מלאה בתמחור ובתנאים
            5. התאמה אישית לצרכי הלקוח
            """
        }
        
        self.knowledge_categories = {
            "investment_types": [
                "מוצרים מובנים",
                "תעודות פיקדון",
                "אגרות חוב מובנות",
                "מוצרי הגנה"
            ],
            "risk_levels": [
                "סיכון נמוך",
                "סיכון בינוני",
                "סיכון גבוה"
            ],
            "investment_terms": [
                "קצר טווח",
                "בינוני טווח",
                "ארוך טווח"
            ]
        }
        
        # Use absolute paths for Heroku
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_path = os.path.join(self.base_dir, "knowledge")
        self.db_path = os.path.join(self.base_dir, "database", "documents.db")
        
        self.setup_logging()
        self.ensure_directories()
        self.setup_database()

    def setup_logging(self):
        """Set up logging configuration for Heroku"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # Stream handler for Heroku logs
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

    def ensure_directories(self):
        """Ensure required directories exist"""
        try:
            os.makedirs(self.knowledge_path, exist_ok=True)
            os.makedirs(os.path.join(self.knowledge_path, "processed"), exist_ok=True)
            os.makedirs(os.path.join(self.knowledge_path, "raw"), exist_ok=True)
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        except Exception as e:
            self.logger.error(f"Error creating directories: {str(e)}")

    def setup_database(self):
        """Initialize SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create documents table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        content TEXT,
                        document_type TEXT,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP,
                        metadata TEXT
                    )
                """)
                
                # Create knowledge_base table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_base (
                        id TEXT PRIMARY KEY,
                        category TEXT,
                        content TEXT,
                        last_updated TIMESTAMP,
                        source TEXT
                    )
                """)
                
                # Create document_tags table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_tags (
                        document_id TEXT,
                        tag TEXT,
                        FOREIGN KEY (document_id) REFERENCES documents(id)
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Database setup error: {str(e)}")
            raise

    def get_core_knowledge(self, knowledge_type: str) -> str:
        """Retrieve core knowledge by type"""
        try:
            if knowledge_type not in self.knowledge_base:
                self.logger.warning(f"Unknown knowledge type requested: {knowledge_type}")
                return ""
            
            knowledge = self.knowledge_base[knowledge_type]
            self.logger.debug(f"Retrieved knowledge for type: {knowledge_type}")
            return knowledge
            
        except Exception as e:
            self.logger.error(f"Error retrieving core knowledge for {knowledge_type}: {str(e)}")
            return ""

    def query_knowledge(self, query: str) -> List[str]:
        """Query knowledge based on user input"""
        try:
            relevant_info = []
            query_lower = query.lower()
            
            # Create keyword mappings
            keyword_mappings = {
                'risk_protection': {
                    'keywords': ['סיכון', 'הגנה', 'בטוח', 'בטחון', 'אבטחה'],
                    'response': """
                    המוצרים שלנו מגיעים עם מנגנוני הגנה מובנים.
                    כל השקעה כרוכה בסיכונים, אך אנו מתמחים בהתאמת רמת הסיכון לצרכי הלקוח.
                    המוצרים שלנו מציעים רמות הגנה שונות בהתאם להעדפות הלקוח.
                    """
                },
                'returns': {
                    'keywords': ['תשואה', 'רווח', 'החזר', 'ריבית', 'רווחים'],
                    'response': """
                    המוצרים שלנו מציעים פוטנציאל תשואה בהתאם לתנאי השוק ורמת הסיכון.
                    אנו מתמחים בבניית מוצרים עם יחס סיכון-תשואה אטרקטיבי.
                    התשואה מותאמת לפרופיל הסיכון של הלקוח ולתנאי השוק.
                    """
                },
                'liquidity': {
                    'keywords': ['נזילות', 'משיכה', 'פדיון', 'זמינות', 'גישה'],
                    'response': """
                    המוצרים שלנו מציעים נזילות יומית עם מחיר מהמנפיק.
                    ניתן לפדות את ההשקעה בכל יום מסחר.
                    אין תקופת נעילה והכסף נשאר נזיל.
                    """
                },
                'process': {
                    'keywords': ['תהליך', 'השקעה', 'להשקיע', 'להתחיל', 'התחלה'],
                    'response': """
                    תהליך ההשקעה מתחיל בפגישת היכרות והתאמה.
                    אנו מתאימים את המוצר לצרכים הספציפיים של כל לקוח.
                    ההשקעה מתבצעת ישירות מול הבנק בחשבון הלקוח.
                    """
                }
            }
            
            # Check for keyword matches
            for category in keyword_mappings.values():
                if any(keyword in query_lower for keyword in category['keywords']):
                    relevant_info.append(category['response'])
            
            return relevant_info
            
        except Exception as e:
            self.logger.error(f"Error querying knowledge: {str(e)}")
            return []

    def get_document_stats(self) -> Dict:
        """Get statistics about processed documents"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {
                    'total_documents': 0,
                    'document_types': defaultdict(int),
                    'tags': defaultdict(int),
                    'latest_update': None
                }
                
                # Count total documents
                cursor.execute("SELECT COUNT(*) FROM documents")
                stats['total_documents'] = cursor.fetchone()[0]
                
                return dict(stats)
                
        except Exception as e:
            self.logger.error(f"Error getting document stats: {str(e)}")
            return {}
