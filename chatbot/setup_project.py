import os
import shutil
from pathlib import Path

def setup_project():
    """Set up the project structure and create necessary files."""
    # Project root directory (where this script is located)
    root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Define the structure
    structure = {
        'src': {
            '__init__.py': 'from .utils.lead_tracker import LeadTracker, show_leads_dashboard, show_conversation\n\n__all__ = ["LeadTracker", "show_leads_dashboard", "show_conversation"]',
            'bot': {
                '__init__.py': '',
                'context.py': None  # None means keep existing file
            },
            'dashboard': {
                '__init__.py': '',
                'analytics.py': None
            },
            'database': {
                '__init__.py': '',
                'models.py': None
            },
            'utils': {
                '__init__.py': 'from .lead_tracker import LeadTracker, show_leads_dashboard, show_conversation\n\n__all__ = ["LeadTracker", "show_leads_dashboard", "show_conversation"]',
                'lead_tracker.py': None
            }
        },
        'config': {
            'client_questionnaire.yaml': None,
            'company_info.yaml': None,
            'legal.yaml': None,
            'products.yaml': None
        },
        'movne_bot.py': None,
        '.env': None,
        'muvne_chat.db': None
    }

    def create_structure(base_path, structure):
        """Recursively create directory structure."""
        for name, content in structure.items():
            path = base_path / name
            
            if isinstance(content, dict):
                # It's a directory
                path.mkdir(exist_ok=True)
                create_structure(path, content)
            elif content is not None:
                # It's a file with content
                if not path.exists() or name == '__init__.py':
                    path.write_text(content)
                    print(f"Created/Updated: {path}")
            else:
                # It's a file to preserve
                if path.exists():
                    print(f"Preserved: {path}")
                else:
                    print(f"Warning: Missing file: {path}")

    def cleanup_unnecessary_files(base_path):
        """Remove unnecessary files and directories."""
        # Files to remove
        patterns_to_remove = [
            '*_init_.py',  # Single underscore init files
            'init_.py',
            '__pycache__',
            '*.pyc'
        ]
        
        for pattern in patterns_to_remove:
            for path in Path(base_path).rglob(pattern):
                if path.is_file():
                    path.unlink()
                    print(f"Removed file: {path}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    print(f"Removed directory: {path}")

    try:
        print("Starting project setup...")
        
        # Clean up unnecessary files first
        print("\nCleaning up unnecessary files...")
        cleanup_unnecessary_files(root_dir)
        
        # Create/verify project structure
        print("\nCreating/verifying project structure...")
        create_structure(root_dir, structure)
        
        print("\nProject setup completed successfully!")
        
    except Exception as e:
        print(f"Error during setup: {str(e)}")

if __name__ == "__main__":
    setup_project()