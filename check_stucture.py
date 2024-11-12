import os
import sys
from pathlib import Path

def check_project_structure():
    """בדיקת מבנה הפרויקט"""
    print("\n=== בדיקת מבנה הפרויקט ===")
    
    current_dir = os.getcwd()
    print(f"\nתיקייה נוכחית: {current_dir}")
    
    # בדיקת תיקיות
    dirs_to_check = {
        'documents1': 'תיקיית מסמכים',
        'src': 'קוד מקור',
        'config': 'הגדרות',
        'admin-panel': 'פאנל ניהול',
        'admin-dashboard': 'דשבורד'
    }
    
    print("\nבדיקת תיקיות:")
    print("-" * 50)
    for dir_name, description in dirs_to_check.items():
        path = os.path.join(current_dir, dir_name)
        exists = os.path.exists(path)
        status = "✓" if exists else "✗"
        print(f"{status} {dir_name:<20} - {description:<20} - {'קיים' if exists else 'חסר'}")
        
        if exists and os.path.isdir(path):
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            if files:
                print("   קבצים:")
                for file in files[:5]:  # מציג רק 5 קבצים ראשונים
                    size = os.path.getsize(os.path.join(path, file)) / 1024
                    print(f"   - {file:<30} ({size:.2f} KB)")
                if len(files) > 5:
                    print(f"   ... ועוד {len(files)-5} קבצים")
            else:
                print("   (תיקייה ריקה)")
        print()
    
    # בדיקת קבצים חשובים
    important_files = [
        'document_processor.py',
        'run_processor.py',
        'setup_project.py',
        'movne_bot.py',
        '.env'
    ]
    
    print("\nבדיקת קבצים חשובים:")
    print("-" * 50)
    for filename in important_files:
        exists = os.path.exists(filename)
        status = "✓" if exists else "✗"
        if exists:
            size = os.path.getsize(filename) / 1024
            print(f"{status} {filename:<30} - קיים ({size:.2f} KB)")
        else:
            print(f"{status} {filename:<30} - חסר")
    
    # בדיקת חבילות Python
    print("\nבדיקת חבילות Python:")
    print("-" * 50)
    packages_to_check = [
        'langchain',
        'langchain-community',
        'sentence-transformers',
        'chromadb',
        'python-dotenv',
        'pypdf',
        'docx2txt',
        'unstructured'
    ]
    
    for package in packages_to_check:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package:<30} - מותקן")
        except ImportError:
            print(f"✗ {package:<30} - חסר")

    print("\n=== המלצות ===")
    print("1. וודא שכל התיקיות והקבצים המסומנים ב-✗ קיימים")
    print("2. התקן חבילות Python חסרות עם pip install")
    print("3. וודא שיש מסמכים בתיקיית documents1")

if __name__ == "__main__":
    try:
        check_project_structure()
    except Exception as e:
        print(f"\nשגיאה בבדיקת מבנה הפרויקט: {str(e)}")