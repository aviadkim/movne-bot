FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir anthropic==0.8.0
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a script to run Streamlit with the correct port
RUN echo '#!/bin/bash\nstreamlit run --server.port $(($PORT)) movne_bot.py' > start.sh
RUN chmod +x start.sh

EXPOSE 8080

CMD ["./start.sh"]
