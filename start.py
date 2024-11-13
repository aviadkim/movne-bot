import os
import subprocess

if __name__ == "__main__":
    # Get the port from environment variable, default to 8080
    port = int(os.environ.get("PORT", 8080))
    
    # Run streamlit with the correct port
    subprocess.run(["streamlit", "run", 
                   "--server.port", str(port),
                   "--server.address", "0.0.0.0",
                   "movne_bot.py"])
