# RFP Studio - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

- **MongoDB Atlas URI**: Your MongoDB connection string
- **OpenAI API Key**: Your OpenAI API key for embeddings and LLM operations
- **Database Name**: MongoDB database name (default: rfp_studio)

### 3. Set up MongoDB Atlas Vector Search

You'll need to create vector search indexes in MongoDB Atlas:

#### For RFP Collection:
```json
{
  "fields": [
    {
      "numDimensions": 1536,
      "path": "embedding",
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}
```

#### For Knowledge Base Collection:
```json
{
  "fields": [
    {
      "numDimensions": 1536,
      "path": "embedding", 
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}
```

### 4. Initialize Knowledge Base

Load sample knowledge for SME routing:

```bash
python cli.py setup-knowledge
```

### 5. Run Example Workflow

Test the complete system:

```bash
python cli.py example
```

## CLI Usage

### Create an RFP
```bash
python cli.py create-rfp --title "My RFP" --client "Acme Corp"
```

### Run Individual Agents
```bash
python cli.py run-agent sales
python cli.py run-agent bdm --rfp-id <rfp_id>
python cli.py run-agent sme_router
```

### Check Configuration
```bash
python cli.py config
```

## Programmatic Usage

```python
import asyncio
from rfp_studio import run_flow

async def main():
    payload = {
        "title": "Enterprise Software RFP", 
        "client_name": "My Company",
        "client_contact": "contact@mycompany.com"
    }
    
    result = await run_flow(payload=payload)
    print(f"Workflow result: {result}")

asyncio.run(main())
```

## Architecture Overview

- **Sales Agent**: Creates/enriches RFP records
- **BDM Agent**: Breaks RFPs into tasks  
- **SME Router**: Routes questions to teams via vector search
- **Writer Agent**: Generates draft content (stub implementation)
- **Legal Agent**: Reviews content for compliance (stub implementation)
- **Quality Agent**: Final QA and validation (stub implementation)

## Development Notes

This is a **skeletal implementation** designed for customer demonstrations. The Writer, Legal, and Quality agents contain stub implementations that would need to be expanded with proper LLM integration for production use.

Key areas for production enhancement:
- Replace stub content generation with LLM calls
- Add comprehensive error handling
- Implement proper logging and monitoring
- Add authentication and authorization
- Expand test coverage
- Add deployment configurations