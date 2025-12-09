# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based AI agent application that helps users find specific cables by querying the EET Group Cable Guide API. The agent uses pydantic-ai with OpenRouter's Mistral model to interpret natural language queries and map them to specific cable connector types.

## Development Commands

### Running the Application
```bash
uvicorn app:app --reload
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Environment Setup
Set the `OPENROUTER_API_KEY` environment variable before running:
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

## Architecture

### Core Components

**FastAPI Application** (`app.py`)
- Single-file application containing the entire service
- Exposes a `/search` endpoint that accepts a `query` parameter
- Returns structured cable query results with `from_connector` and `to_connector` fields

**AI Agent Flow**
The agent follows a strict two-step tool calling pattern:
1. Calls `get_cable_ends_a()` to retrieve all available "from" connector types
2. Calls `get_cable_ends_b(cable_end_a)` ONCE with the selected connector to get compatible "to" connectors
3. Returns a `CableQuery` with both connector types, or empty strings if no match exists

**EET API Integration**
Both tool functions query the EET Group Cable Guide API:
- Endpoint A: `https://api.eetgroup.com/api/CableGuide/GetCableEndTypesA`
- Endpoint B: `https://api.eetgroup.com/api/CableGuide/GetCableEndTypesB?cableEndTypeA={id}`
- Required headers include culture, business entity ID, market ID, and site ID

### Important Constraints

**Agent System Prompt Rules**
- The agent MUST call `get_cable_ends_b` exactly once (enforced in system prompt)
- If no match is found in `get_cable_ends_b`, the cable combination doesn't exist
- Default to "male" connectors when gender is ambiguous in user queries
- Never fabricate cable connector names

**Model Configuration**
- Uses `mistralai/mistral-large-2512` via OpenRouter
- Output type is strictly typed as `CableQuery` (Pydantic model)

## Key Implementation Details

The `get_cable_ends_a` function currently returns a hardcoded list (line 20) but includes commented-out API call logic (lines 21-38). When uncommenting the API logic, remove the hardcoded return statement on line 20.

The system is designed to prevent hallucination by requiring exact matches from the API responses - the agent cannot suggest cables that don't exist in the EET catalog.

## Google Custom Search Integration

The agent can optionally search Google Custom Search API to identify cable requirements for specific products.

### Environment Variables

**Required for search functionality:**
- `GOOGLE_API_KEY` - Your Google Cloud API key with Custom Search API enabled
- `GOOGLE_CSE_ID` - Your Custom Search Engine ID

See `.env.example` for configuration template.

### When Search is Used

The agent autonomously decides to use search when:
- User mentions product names (e.g., "iPhone 15", "MacBook Pro", "PS5")
- Query includes device models or brand names
- Additional context would help identify the correct cable

**Examples:**
- "What cable does iPhone 15 use?" → Uses search
- "HDMI to USB-C cable" → Skips search (direct cable query)
- "MacBook Air charging cable" → Uses search

### How It Works

1. **search_product_info tool** queries Google Custom Search API
2. **Connector extraction** uses regex to identify cable types in search results (USB-C, HDMI, Lightning, etc.)
3. **Agent validates** extracted connectors against the EET catalog using get_cable_ends_a/b
4. **Returns CableQuery** with validated connector types or empty strings if not found

### Search Limitations

- Search results inform the agent but don't override EET API validation
- If search fails (no API keys, timeout, rate limit), agent falls back to direct cable lookup
- Rate limits apply based on Google API quota (100 free queries/day, then paid)
- Search requires internet connectivity and valid API credentials

### Cost Considerations

**Google Custom Search API Pricing:**
- Free tier: 100 queries per day
- Paid tier: $5 per 1,000 queries beyond free tier

Consider implementing caching for repeated product searches to reduce costs.
