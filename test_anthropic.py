import anthropic
import sys
from dotenv import load_dotenv
import os

def test_anthropic_connection():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get API key from environment variable
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not found in environment variables")
            return False
            
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": "Please respond with 'Connection successful' if you receive this message."
            }]
        )
        
        print("API Response:", message.content[0].text)
        return True
    except Exception as e:
        print("Error:", str(e))
        return False

if __name__ == "__main__":
    success = test_anthropic_connection()
    sys.exit(0 if success else 1)