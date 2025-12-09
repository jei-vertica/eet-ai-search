# Getting Started Guide

This guide will walk you through setting up and running the EET AI Cable Search application.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- OpenRouter API key (required)
- Google Custom Search API credentials (optional, for product search feature)

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd eet-ai-search
```

## Step 2: Set Up Python Virtual Environment

Creating a virtual environment isolates the project dependencies from your system Python installation.

```bash
# Create virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

You should see `(venv)` appear in your terminal prompt, indicating the virtual environment is active.

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- fastapi - Web framework
- uvicorn - ASGI server
- pydantic-ai - AI agent framework
- httpx - HTTP client for API calls

## Step 4: Configure Environment Variables

You need to set up API keys for the application to work.

### Required: OpenRouter API Key

The application requires an OpenRouter API key to use the Mistral AI model.

1. Get an API key from [OpenRouter](https://openrouter.ai/)
2. Set the environment variable:

```bash
export OPENROUTER_API_KEY="your-openrouter-key-here"
```

### Optional: Google Custom Search API

To enable product search functionality (e.g., "What cable does iPhone 15 use?"), you need Google Custom Search API credentials.

**Get Google API Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Custom Search API"
4. Create credentials (API Key)
5. Copy your API key

**Create Custom Search Engine:**
1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Configure it to search the entire web
4. Copy your Search Engine ID (cx parameter)

**Set environment variables:**

```bash
export GOOGLE_API_KEY="your-google-api-key-here"
export GOOGLE_CSE_ID="your-custom-search-engine-id-here"
```

**Note:** If you don't set these variables, the application will still work, but product-based queries will fall back to direct cable lookup without web search.

### Making Environment Variables Persistent

To avoid setting these every time, add them to your shell configuration file:

```bash
# For bash users, add to ~/.bashrc:
echo 'export OPENROUTER_API_KEY="your-key-here"' >> ~/.bashrc
echo 'export GOOGLE_API_KEY="your-key-here"' >> ~/.bashrc
echo 'export GOOGLE_CSE_ID="your-cse-id-here"' >> ~/.bashrc
source ~/.bashrc

# For zsh users, add to ~/.zshrc:
echo 'export OPENROUTER_API_KEY="your-key-here"' >> ~/.zshrc
echo 'export GOOGLE_API_KEY="your-key-here"' >> ~/.zshrc
echo 'export GOOGLE_CSE_ID="your-cse-id-here"' >> ~/.zshrc
source ~/.zshrc
```

Alternatively, create a `.env` file (see `.env.example`) and use a tool like `python-dotenv` or manually source it before running.

## Step 5: Start the Application

Make sure your virtual environment is activated and environment variables are set, then run:

```bash
uvicorn app:app --reload
```

Or if `uvicorn` is not in your PATH:

```bash
python -m uvicorn app:app --reload
```

You should see output like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

The `--reload` flag enables auto-reloading when you make code changes during development.

## Step 6: Test the Application

### Using curl

**Test a direct cable query (no web search):**
```bash
curl "http://localhost:8000/search?query=HDMI%20to%20USB-C%20cable"
```

**Test a product-based query (uses web search if configured):**
```bash
curl "http://localhost:8000/search?query=What%20cable%20does%20iPhone%2015%20use"
```

### Using a web browser

Navigate to:
- Direct cable query: `http://localhost:8000/search?query=HDMI to USB-C cable`
- Product query: `http://localhost:8000/search?query=What cable does iPhone 15 use`

### Expected Response Format

```json
{
  "from_connector": "HDMI Male",
  "to_connector": "USB C Male"
}
```

If no matching cable is found in the EET catalog:
```json
{
  "from_connector": "",
  "to_connector": ""
}
```

## Step 7: View API Documentation

FastAPI provides automatic API documentation. While the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### Error: "Set the OPENROUTER_API_KEY environment variable"

**Solution:** Make sure you've exported the OPENROUTER_API_KEY before starting the server. You can verify it's set with:
```bash
echo $OPENROUTER_API_KEY
```

### Error: "uvicorn: command not found"

**Solution:** Make sure your virtual environment is activated:
```bash
source venv/bin/activate
```

Or use the Python module syntax:
```bash
python -m uvicorn app:app --reload
```

### Error: "Google Custom Search not configured"

**Solution:** This is a warning, not an error. The application will work without Google API credentials, but product-based queries won't use web search. To enable search, set `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` environment variables.

### Virtual environment not activating

**On Linux/macOS:**
```bash
source venv/bin/activate
```

**On Windows Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

**On Windows PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

### Port already in use

If port 8000 is already in use, specify a different port:
```bash
uvicorn app:app --reload --port 8001
```

## Stopping the Server

Press `CTRL+C` in the terminal where the server is running.

## Deactivating the Virtual Environment

When you're done working on the project:

```bash
deactivate
```

## Quick Reference

```bash
# Complete setup and run sequence
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENROUTER_API_KEY="your-key-here"
export GOOGLE_API_KEY="your-key-here"  # optional
export GOOGLE_CSE_ID="your-cse-id-here"  # optional
uvicorn app:app --reload
```

## Next Steps

- Review `CLAUDE.md` for architecture details and development guidance
- Explore the `/search` endpoint with different cable queries
- Check console output to see agent tool calls and decision-making process
- Review `app.py` to understand the agent's system prompt and tool implementations

## Cost Considerations

**OpenRouter:** Pricing depends on the model used (currently `mistralai/mistral-large-2512`). Check [OpenRouter pricing](https://openrouter.ai/docs#models) for current rates.

**Google Custom Search API:**
- Free tier: 100 queries per day
- Paid tier: $5 per 1,000 queries beyond free tier

Monitor your usage on respective platforms to avoid unexpected costs.
