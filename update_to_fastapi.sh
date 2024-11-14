#!/bin/bash

# Update requirements.txt
echo "Updating requirements.txt..."
sed -i '/streamlit/d' requirements.txt
echo "fastapi==0.68.0" >> requirements.txt
echo "uvicorn==0.15.0" >> requirements.txt

# Update Dockerfile
echo "Updating Dockerfile..."
sed -i 's/CMD streamlit run --server.port $PORT app.py/CMD uvicorn app:app --host 0.0.0.0 --port $PORT/' Dockerfile

# Update Procfile (if it exists)
if [ -f "Procfile" ]; then
    echo "Updating Procfile..."
    sed -i 's/web: streamlit run --server.port $PORT app.py/web: uvicorn app:app --host 0.0.0.0 --port $PORT/' Procfile
fi

# Update app.py
echo "Updating app.py..."
cat > app.py << EOL
from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Add your other FastAPI routes and logic here

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOL

echo "Changes completed. Please review the modified files to ensure everything is correct."
