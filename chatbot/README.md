# Movne Bot - Investment Marketing Assistant

A Streamlit-based chatbot application for investment marketing assistance, powered by Claude AI.

## Project Structure
```
movne_bot/
├── src/
│   ├── bot/
│   │   └── context.py
│   ├── database/
│   │   └── models.py
│   └── utils/
│       ├── document_processor.py
│       └── lead_tracker.py
├── config/
│   ├── company_info.yaml
│   ├── products.yaml
│   ├── legal.yaml
│   └── sales_responses.yaml
├── movne_bot.py
├── requirements.txt
├── Procfile
└── runtime.txt
```

## Setup Instructions

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/movne_bot.git
cd movne_bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with required environment variables:
```
ANTHROPIC_API_KEY=your_api_key_here
```

5. Run the application:
```bash
streamlit run movne_bot.py
```

### Deployment to Heroku

1. Create a new Heroku app:
```bash
heroku create your-app-name
```

2. Set environment variables:
```bash
heroku config:set ANTHROPIC_API_KEY=your_api_key_here
```

3. Deploy to Heroku:
```bash
git push heroku main
```

## Features

- Real-time chat interface with Claude AI
- Hebrew language support with RTL text direction
- Document processing and knowledge base integration
- Conversation history tracking
- Investment product information management
- Compliance with financial regulations

## Configuration

The application uses YAML configuration files in the `config/` directory:
- `company_info.yaml`: Company details and policies
- `products.yaml`: Investment product information
- `legal.yaml`: Legal disclaimers and requirements
- `sales_responses.yaml`: Pre-defined response templates

## Environment Variables

Required environment variables:
- `ANTHROPIC_API_KEY`: API key for Claude AI integration

## Development Guidelines

1. Follow PEP 8 style guidelines
2. Add appropriate error handling
3. Update requirements.txt when adding new dependencies
4. Test thoroughly before deployment

## License

This project is proprietary and confidential.
