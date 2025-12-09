from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
import json
import httpx
import os
import re

app = FastAPI()

# Load environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

# Define models
class CableQuery(BaseModel):
    from_connector: str
    to_connector: str

# Define tools based on instrumentation (real for get_cable_types)
async def get_cable_ends_a(ctx: RunContext) -> list[str]:
    print("calling get_cable_ends_a")
    return ["2.5mm Female", "2.5mm Male", "3.5mm Female", "3.5mm Male", "6.35mm Female", "6.35mm Male", "Power Type I - Australia Male", "BNC Female", "BNC Male", "Power Type N - Brazil Female", "Power Type N - Brazil Male", "Power Type C13 Female", "Power Type C14 Male", "Power Type C15 Female", "Power Type C19 Female", "Power Type C20 Male", "C21 coupler Female", "Power Type C5 Female", "Power Type C7 Female", "DB25 Female", "DB25 Male", "DB9 Female", "DB9 Male", "Power Type K - Denmark Female", "Power Type K - Denmark Male", "Powerstrip Type K - Denmark", "DisplayPort Female", "DisplayPort Male", "DVI-D Female", "DVI-D Male", "DVI-I Female", "DVI-I Male", "E2000 Male", "Power Type C - EU Male", "FC Male", "Powerstrip Type E - French", "HDMI Female", "HDMI Male", "HDMI Micro Male", "HDMI Mini Female", "HDMI Mini Male", "IEC Female", "IEC Male", "Power Type D - India Male", "Power Type L - Italy Male", "LC Female", "LC Male", "Lightning Female", "Lightning Male", "Mini DisplayPort Female", "Mini DisplayPort Male", "MPO/MTP Female", "MPO/MTP Male", "MTRJ Male", "MU/UPC Male", "Multi Male", "Open End", "PS/2 Female", "PS/2 Male", "QSFP+ Male", "RCA Female", "RCA Male", "RJ11 Female", "RJ11 Male", "RJ12 Male", "RJ45 Female", "RJ45 Male", "RP-SMA Female", "RP-SMA Male", "SATA 15-pin Female", "SATA 15-pin Male", "SATA 7-pin Female", "SATA 7-pin Male", "SC Female", "SC Male", "Power Type E/F - Schuko Female", "Power Type E/F - Schuko Male", "Powerstrip Type F - Schuko", "SFF Male", "SFP Male", "Power Type M - South Africa Male", "Speaker Raw Cable Male", "ST Male", "ST/UPC Male", "Power Type J - Switzerland Female", "Power Type J - Switzerland Male", "Thunderbolt Male", "TOSLINK Male", "Power Type G - UK Male", "Powerstrip Type G - UK", "Power Type A - USA Male", "Power Type B - USA Male", "USB A Female", "USB A Male", "USB B Female", "USB B Male", "USB C Female", "USB C Male", "USB Micro A Male", "USB Micro B Female", "USB Micro B Male", "USB Mini B Male", "VGA Female", "VGA Male", "XLR (3-pin) Female", "XLR (3-pin) Male"]
    url = 'https://api.eetgroup.com/api/CableGuide/GetCableEndTypesA'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'identity',
        'Content-Type': 'application/json',
        'x-eet-culture': 'en-zz',
        'x-eet-businessentityid': '9',
        'x-eet-marketid': '1006',
        'x-eet-siteid': '23',
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        data = response.json()
        # Extract names from cableTypes
        if 'model' in data and 'cableTypes' in data['model']:
            return [item['id'] for item in data['model']['cableTypes'] if 'id' in item]
        return []

async def get_cable_ends_b(ctx: RunContext, cable_end_a: str) -> list[str]:
    print(f"calling the get_cable_ends_b with {cable_end_a}")
    url = f'https://api.eetgroup.com/api/CableGuide/GetCableEndTypesB?cableEndTypeA={cable_end_a}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'identity',
        'Content-Type': 'application/json',
        'x-eet-culture': 'en-zz',
        'x-eet-businessentityid': '9',
        'x-eet-marketid': '1006',
        'x-eet-siteid': '23',
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        data = response.json()
        # Extract names from cableTypes
        if 'model' in data and 'cableTypes' in data['model']:
            out = [item['id'] for item in data['model']['cableTypes'] if 'id' in item]
            print(out)
            return out
        return []

def extract_connector_types(search_data: dict) -> list[str]:
    """
    Extract cable connector types from Google search results.

    Strategy:
    1. Collect all text from titles, snippets, and page text
    2. Match against common connector patterns
    3. Return unique matches in order of confidence

    Args:
        search_data: JSON response from Google Custom Search API

    Returns:
        List of detected connector types (e.g., ["HDMI", "USB-C", "Lightning"])
    """
    # Common connector patterns to search for
    connector_patterns = [
        # USB variants
        r'\bUSB[\s-]?C\b', r'\bUSB-C\b', r'\bUSB Type-C\b',
        r'\bUSB[\s-]?A\b', r'\bUSB-A\b', r'\bUSB Type-A\b',
        r'\bUSB[\s-]?B\b', r'\bUSB-B\b',
        r'\bUSB[\s-]?Micro\b', r'\bMicro USB\b',
        r'\bUSB[\s-]?Mini\b', r'\bMini USB\b',

        # Display connectors
        r'\bHDMI\b',
        r'\bDisplayPort\b', r'\bDP\b',
        r'\bMini DisplayPort\b', r'\bMini DP\b',
        r'\bDVI[-]?[DI]?\b',
        r'\bVGA\b',

        # Apple/Mobile
        r'\bLightning\b',
        r'\bThunderbolt\b',

        # Audio
        r'\b3\.5mm\b', r'\b3\.5\s?mm\b', r'\bheadphone jack\b',
        r'\b6\.35mm\b', r'\b1/4["\s]inch\b',
        r'\b2\.5mm\b',
        r'\bXLR\b',
        r'\bRCA\b',

        # Networking
        r'\bRJ45\b', r'\bRJ-45\b', r'\bEthernet\b',
        r'\bRJ11\b', r'\bRJ-11\b',

        # Power
        r'\bPower Type [A-Z]\b',
        r'\bIEC\b',
        r'\bSchuko\b',

        # Other
        r'\bBNC\b',
        r'\bSATA\b',
        r'\beSATA\b',
    ]

    # Collect all searchable text
    text_corpus = []
    if "items" in search_data:
        for item in search_data["items"]:
            if "title" in item:
                text_corpus.append(item["title"])
            if "snippet" in item:
                text_corpus.append(item["snippet"])
            if "htmlSnippet" in item:
                text_corpus.append(item["htmlSnippet"])

    combined_text = " ".join(text_corpus)

    # Find matches
    found_connectors = []
    seen = set()

    for pattern in connector_patterns:
        matches = re.finditer(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            # Normalize the match
            connector = match.group(0).strip()
            connector_normalized = connector.upper().replace("-", " ").replace("  ", " ")

            if connector_normalized not in seen:
                found_connectors.append(connector)
                seen.add(connector_normalized)

    return found_connectors[:10]  # Limit to top 10 unique connectors

async def search_product_info(ctx: RunContext, product_query: str) -> dict:
    """
    Search Google Custom Search API for product cable information.

    Args:
        ctx: RunContext from pydantic-ai
        product_query: Search query (e.g., "iPhone 15 Pro cable connectors")

    Returns:
        dict with structure:
        {
            "success": bool,
            "connector_types": list[str],  # Extracted connector types
            "snippets": list[str],  # Top 3 result snippets for context
            "error": str | None
        }
    """
    print(f"Calling search_product_info with query: {product_query}")

    # Validate configuration
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return {
            "success": False,
            "connector_types": [],
            "snippets": [],
            "error": "Google Custom Search not configured. Set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables."
        }

    # Build Google Custom Search API URL
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": product_query,
        "num": 5  # Fetch top 5 results for better connector extraction
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract connector types from search results
            connector_types = extract_connector_types(data)

            # Get top 3 snippets for agent context
            snippets = []
            if "items" in data:
                for item in data["items"][:3]:
                    if "snippet" in item:
                        snippets.append(item["snippet"])

            return {
                "success": True,
                "connector_types": connector_types,
                "snippets": snippets,
                "error": None
            }

    except httpx.HTTPStatusError as e:
        error_msg = f"Google API HTTP error: {e.response.status_code}"
        if e.response.status_code == 429:
            error_msg += " - Rate limit exceeded"
        elif e.response.status_code == 403:
            error_msg += " - Invalid API key or CSE ID"
        print(error_msg)
        return {
            "success": False,
            "connector_types": [],
            "snippets": [],
            "error": error_msg
        }
    except httpx.TimeoutException:
        error_msg = "Google API request timed out"
        print(error_msg)
        return {
            "success": False,
            "connector_types": [],
            "snippets": [],
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "connector_types": [],
            "snippets": [],
            "error": error_msg
        }

# Agent setup
model = OpenRouterModel(
    'mistralai/mistral-large-2512',
    provider=OpenRouterProvider(api_key=os.getenv('OPENROUTER_API_KEY')),
)
agent = Agent(
    model,
    system_prompt="""READ THE WHOLE SYSTEM_PROMPT VERY CAREFULLY.

You are an agent that helps users find specific cables. You have three tools available:

1. search_product_info(product_query): Search Google for product cable information
2. get_cable_ends_a(): Get all available cable connector types from EET catalog
3. get_cable_ends_b(cable_end_a): Get compatible connector types for a given connector

YOUR DECISION PROCESS:

STEP 1 - Analyze the query:
- If the user mentions a PRODUCT NAME (e.g., "iPhone 15", "MacBook Pro", "PS5"), use search_product_info FIRST to find what connectors that product uses
- If the user describes a cable DIRECTLY (e.g., "HDMI to USB-C cable", "lightning to USB-A"), skip search and go directly to cable lookup

STEP 2 - Cable lookup process:
- Call get_cable_ends_a() to get all available connector types
- Pick the best match for the FIRST connector end from the query or search results
- Call get_cable_ends_b(cable_end_a) ONCE and ONLY ONCE with your selected connector
- DO NOT call get_cable_ends_b more than once under any circumstances

STEP 3 - Interpret results:
- If get_cable_ends_b returns no matches, the cable combination doesn't exist in the EET catalog
- Tell the user clearly if the cable doesn't exist
- Never fabricate connector names

IMPORTANT RULES:
- If gender (male/female) isn't specified, assume male where it makes sense
- Be certain the cable actually exists before confirming
- Use search results to inform your connector selection, but final connectors MUST come from the EET API (get_cable_ends_a and get_cable_ends_b)
- If search fails, proceed with cable lookup using the query directly
- Return empty strings if you cannot find a match

EXAMPLES:

Query: "What cable do I need for iPhone 15?"
Action: search_product_info("iPhone 15 cable connectors") → find "USB-C" and "Lightning" → proceed with cable lookup

Query: "HDMI to DisplayPort cable"
Action: Skip search → get_cable_ends_a() → select "HDMI Male" → get_cable_ends_b("HDMI Male") → find match

Query: "MacBook Air M2 charging cable"
Action: search_product_info("MacBook Air M2 charging cable") → find "MagSafe 3" or "USB-C" → proceed with cable lookup
""",
    output_type=CableQuery,
)

# Add tools
agent.tool(get_cable_ends_a)
agent.tool(get_cable_ends_b)
agent.tool(search_product_info)

@app.get("/search")
async def search(query: str):
    result = await agent.run(query)
    return result.output
