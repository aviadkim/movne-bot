import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import json
from pathlib import Path
import os
from ruamel.yaml import YAML
yaml = YAML(typ='safe')

def apply_rtl_design():
    """Apply RTL design to Streamlit components"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700&display=swap');

    /* כללי */
    * {
        font-family: 'Heebo', sans-serif !important;
        direction: rtl !important;
    }

    /* תיקון כותרות */
    h1, h2, h3 {
        color: #1a1a1a;
        text-align: right !important;
        font-weight: 700 !important;
        margin-bottom: 2rem !important;
    }

    /* תיקון שדות קלט */
    .stTextInput label {
        text-align: right !important;
        width: 100% !important;
        color: #1a1a1a !important;
        font-weight: 500 !important;
    }

    .stTextInput input {
        text-align: right !important;
        border-radius: 4px !important;
        border: 1px solid #e0e0e0 !important;
        background-color: #f8f9fa !important;
    }

    /* תיקון תיבות בחירה */
    .stSelectbox label {
        text-align: right !important;
        width: 100% !important;
        color: #1a1a1a !important;
        font-weight: 500 !important;
    }

    .stSelectbox > div > div {
        text-align: right !important;
    }

    /* תיקון צ'קבוקסים */
    .stCheckbox {
        text-align: right !important;
    }

    .stCheckbox > div {
        flex-direction: row-reverse !important;
        justify-content: flex-end !important;
    }

    .stCheckbox label {
        margin-right: 0 !important;
        margin-left: 10px !important;
        color: #1a1a1a !important;
    }

    /* הוספת רקע לבן לטפסים */
    .form-container {
        background-color: white;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }

    /* סגנון כפתור שליחה */
    .stButton > button {
        background-color: #1a237e !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 2rem !important;
        border-radius: 4px !important;
        float: left !important;
    }

    /* תיקון סרגל צד */
    .css-1d391kg {
        direction: rtl !important;
    }

    /* כותרות סקציות */
    .section-header {
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
        color: #1a1a1a;
        font-weight: 700;
    }

    /* עיצוב שדה מספר */
    .stNumberInput {
        direction: ltr !important;
    }

    .stNumberInput label {
        text-align: right !important;
        width: 100% !important;
    }

    /* תיקון מרווחים */
    .block-container {
        padding-top: 2rem !important;
        max-width: 1000px !important;
    }

    /* סרגל צידי */
    .css-1544g2n {
        padding: 2rem 1rem !important;
    }

    .css-1544g2n > div {
        direction: rtl !important;
        text-align: right !important;
    }
    </style>
    """, unsafe_allow_html=True)
class DigitalForms:
    def __init__(self):
        self.setup_database()
        self.logo_path = Path(__file__).parent / "logo.png"  

    def setup_database(self):
        """Initialize database for storing form submissions"""
        conn = sqlite3.connect('forms.db')
        c = conn.cursor()
        
        # Qualified Investor Declaration table
        c.execute('''CREATE TABLE IF NOT EXISTS qualified_investor_declarations
                    (id TEXT PRIMARY KEY,
                     submission_date DATETIME,
                     investor_details JSON,
                     financial_criteria JSON,
                     digital_signature TEXT,
                     status TEXT)''')
                     
        # Marketing Agreement table
        c.execute('''CREATE TABLE IF NOT EXISTS marketing_agreements
                    (id TEXT PRIMARY KEY,
                     submission_date DATETIME,
                     client_details JSON,
                     agreement_details JSON,
                     digital_signature TEXT,
                     status TEXT)''')
                     
        conn.commit()
        conn.close()

    def marketing_agreement_form(self):
        st.title("הסכם שיווק השקעות")
        
        with st.form("marketing_agreement"):
            # פרטי לקוח
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">פרטי לקוח</h3>', unsafe_allow_html=True)
            
            # שורה ראשונה - שם מלא
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("שם פרטי")
            with col2:
                last_name = st.text_input("שם משפחה")
                
            # שורה שנייה - פרטי קשר
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("דואר אלקטרוני")
            with col2:
                phone = st.text_input("טלפון")
                
            address = st.text_input("כתובת")
            id_number = st.text_input("מספר זהות")
            st.markdown('</div>', unsafe_allow_html=True)

            # שאלון מנספח ב'
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">שאלון לקוח ומדיניות השקעות</h3>', unsafe_allow_html=True)
            
            relationship = st.radio(
                "מהות הקשר בין בעלי החשבון",
                ["זוג", "אחר"]
            )
            
            if relationship == "אחר":
                other_relationship = st.text_input("פרט:")
            
            marital_status = st.selectbox(
                "מצב משפחתי",
                ["רווק/ה", "נשוי/אה", "גרוש/ה", "אלמן/ה"]
            )
            
            employment_status = st.selectbox(
                "מצב תעסוקתי",
                ["שכיר/ה", "עצמאי/ת", "פנסיונר/ית", "אחר"]
            )

            st.write("המטרה העיקרית של ההשקעה:")
            investment_goals = st.multiselect(
                "",
                ["שמירה על הכסף", "חיסכון לטווח ארוך", "הגדלת ההון", "יצירת הכנסה שוטפת"]
            )
            
            investment_horizon = st.selectbox(
                "טווח ההשקעה הצפוי",
                ["עד שנתיים", "2-5 שנים", "מעל 5 שנים", "לא מוגבל"]
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # פרופיל השקעות
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">פרופיל השקעות</h3>', unsafe_allow_html=True)
            
            investment_experience = st.selectbox(
                "ניסיון בהשקעות",
                ["בחר...", "אין ניסיון", "1-3 שנים", "3-5 שנים", "מעל 5 שנים"]
            )
            
            risk_tolerance = st.selectbox(
                "רמת סיכון מבוקשת",
                ["בחר...", "נמוכה", "בינונית", "גבוהה"]
            )
            
            investment_amount = st.number_input(
                "סכום השקעה מתוכנן (בש\"ח)",
                min_value=0,
                step=10000
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # גילוי נאות וחתימה
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">גילוי נאות</h3>', unsafe_allow_html=True)
            st.markdown("""
            1. מובנה גלובל הינה חברה בעלת רישיון שיווק השקעות מטעם רשות ניירות ערך.
            2. החברה מתמחה במוצרים פיננסיים מובנים ופועלת בשקיפות מלאה מול לקוחותיה.
            3. כל השקעה כרוכה בסיכונים והחברה אינה מתחייבת לתשואה כלשהי.
            4. המידע המוצג אינו מהווה המלצה או הצעה לרכישת ניירות ערך.
            5. ההשקעה במוצרים מובנים מיועדת למשקיעים כשירים בלבד.
            """)
            
            agreement_confirmation = st.checkbox("אני מאשר/ת את כל התנאים הנ\"ל")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # חתימה דיגיטלית
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">חתימה דיגיטלית</h3>', unsafe_allow_html=True)
            signature = st.text_input("אנא הקלד את שמך המלא כחתימה דיגיטלית")
            st.markdown('</div>', unsafe_allow_html=True)
            
            submitted = st.form_submit_button("שלח טופס")
            
            if submitted:
                if not all([first_name, last_name, email, phone, agreement_confirmation, signature]):
                    st.error("נא למלא את כל שדות החובה")
                else:
                    form_data = {
                        'client_details': {
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email,
                            'phone': phone,
                            'address': address,
                            'id_number': id_number,
                            'relationship': relationship,
                            'marital_status': marital_status,
                            'employment_status': employment_status,
                            'investment_goals': investment_goals,
                            'investment_horizon': investment_horizon
                        },
                        'investment_profile': {
                            'experience': investment_experience,
                            'risk_tolerance': risk_tolerance,
                            'investment_amount': investment_amount
                        },
                        'confirmations': {
                            'agreement_confirmed': agreement_confirmation
                        },
                        'signature': signature,
                        'submission_date': datetime.now().isoformat()
                    }
                    
                    self.save_marketing_agreement(form_data)
                    st.success("הטופס נשלח בהצלחה!")

    def qualified_investor_form(self):
        st.title("הצהרת משקיע כשיר")
        
        with st.form("qualified_investor"):
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">פרטי המשקיע</h3>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("שם פרטי")
            with col2:
                last_name = st.text_input("שם משפחה")
                
            email = st.text_input("דואר אלקטרוני")
            phone = st.text_input("טלפון")
            id_number = st.text_input("מספר זהות")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">קריטריונים להשקעה</h3>', unsafe_allow_html=True)
            
            criteria = st.multiselect(
                "סמן את כל הקריטריונים המתאימים:",
                [
                    "השווי הכולל של מזומנים,פקדונות,נכסים פיננסים וניירות ערך שבבעלותי עולה על 8,364,177 שח "
                    "גובה הכנסתי השנתית, בכל אחת מהשנתיים האחרונות עולה על 1,254,627 שח או הכנסת התא המשפחתי אליו אני משתייך עולה על 1,881,940 שח",
                    "השווי הכולל של הנכסים הנזילים שבבעלותי עולה על 5,227,610 שח וגם גובה הכנסתי השנתית, בכל אחת מהשנתיים האחרונות עולה על 627,313 שח ליחיד או 940969 שח להכנסת התא המשפחתי אליו אני משתייך",
                    "ניסיון מקצועי רלוונטי בשוק ההון"
                ]
            )
            
            experience = st.selectbox(
                "ניסיון בשוק ההון",
                ["אין ניסיון", "1-3 שנים", "3-5 שנים", "מעל 5 שנים"]
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">הצהרה</h3>', unsafe_allow_html=True)
            declaration = st.checkbox("אני מצהיר/ה שכל הפרטים שמסרתי נכונים")
            signature = st.text_input("חתימה דיגיטלית (הקלד שם מלא)")
            st.markdown('</div>', unsafe_allow_html=True)
            
            submitted = st.form_submit_button("שלח טופס")
            
            if submitted:
                if not all([first_name, last_name, email, phone, criteria, declaration, signature]):
                    st.error("נא למלא את כל שדות החובה")
                else:
                    form_data = {
                        'investor_details': {
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email,
                            'phone': phone,
                            'id_number': id_number
                        },
                        'financial_criteria': {
                            'selected_criteria': criteria,
                            'experience': experience
                        },
                        'signature': signature,
                        'submission_date': datetime.now().isoformat()
                    }
                    self.save_qualified_investor(form_data)
                    st.success("הטופס נשלח בהצלחה!")

    def save_qualified_investor(self, investor_data):
        """Save qualified investor declaration to database"""
        conn = sqlite3.connect('forms.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO qualified_investor_declarations 
                    (id, submission_date, investor_details, financial_criteria, 
                     digital_signature, status)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (str(datetime.now().timestamp()),
                  investor_data['submission_date'],
                  json.dumps(investor_data['investor_details']),
                  json.dumps(investor_data['financial_criteria']),
                  investor_data['signature'],
                  'submitted'))
              
        conn.commit()
        conn.close()

    def save_marketing_agreement(self, agreement_data):
        """Save marketing agreement to database"""
        conn = sqlite3.connect('forms.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO marketing_agreements 
                    (id, submission_date, client_details, agreement_details, 
                     digital_signature, status)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (str(datetime.now().timestamp()),
                  agreement_data['submission_date'],
                  json.dumps(agreement_data['client_details']),
                  json.dumps(agreement_data['investment_profile']),
                  agreement_data['signature'],
                  'signed'))
              
        conn.commit()
        conn.close()

def main():
    st.set_page_config(page_title="מובנה גלובל - טפסים", layout="wide")
    apply_rtl_design()
    
    forms = DigitalForms()
    
    # Navigation
    form_type = st.sidebar.radio(
        "בחר טופס",
        ["הצהרת משקיע כשיר", "הסכם שיווק השקעות"]
    )
    
    if form_type == "הצהרת משקיע כשיר":
        forms.qualified_investor_form()
    else:
        forms.marketing_agreement_form()

if __name__ == "__main__":
    main()