from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from typing import Literal, Union, TypedDict
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

# New response models with discriminator
class CableResponse(BaseModel):
    response_type: Literal["cable"] = "cable"
    from_connector: str
    to_connector: str

class OrderStatusResponse(BaseModel):
    response_type: Literal["order"] = "order"
    summary: str
    order_id: str | None = None

# Union type for agent output
AgentResponse = Union[CableResponse, OrderStatusResponse]

# Dependencies for passing API parameters to tools
class AgentDependencies(TypedDict):
    customer_id: str
    language: str
    erp_business_entity_id: int

# Define tools based on instrumentation (real for get_cable_types)
async def get_cable_ends_a(ctx: RunContext[AgentDependencies]) -> list[str]:
    print("calling get_cable_ends_a")
    return ["2.5mm Female", "2.5mm Male", "3.5mm Female", "3.5mm Male", "6.35mm Female", "6.35mm Male", "Power Type I - Australia Male", "BNC Female", "BNC Male", "Power Type N - Brazil Female", "Power Type N - Brazil Male", "Power Type C13 Female", "Power Type C14 Male", "Power Type C15 Female", "Power Type C19 Female", "Power Type C20 Male", "C21 coupler Female", "Power Type C5 Female", "Power Type C7 Female", "DB25 Female", "DB25 Male", "DB9 Female", "DB9 Male", "Power Type K - Denmark Female", "Power Type K - Denmark Male", "Powerstrip Type K - Denmark", "DisplayPort Female", "DisplayPort Male", "DVI-D Female", "DVI-D Male", "DVI-I Female", "DVI-I Male", "E2000 Male", "Power Type C - EU Male", "FC Male", "Powerstrip Type E - French", "HDMI Female", "HDMI Male", "HDMI Micro Male", "HDMI Mini Female", "HDMI Mini Male", "IEC Female", "IEC Male", "Power Type D - India Male", "Power Type L - Italy Male", "LC Female", "LC Male", "Lightning Female", "Lightning Male", "Mini DisplayPort Female", "Mini DisplayPort Male", "MPO/MTP Female", "MPO/MTP Male", "MTRJ Male", "MU/UPC Male", "Multi Male", "Open End", "PS/2 Female", "PS/2 Male", "QSFP+ Male", "RCA Female", "RCA Male", "RJ11 Female", "RJ11 Male", "RJ12 Male", "RJ45 Female", "RJ45 Male", "RP-SMA Female", "RP-SMA Male", "SATA 15-pin Female", "SATA 15-pin Male", "SATA 7-pin Female", "SATA 7-pin Male", "SC Female", "SC Male", "Power Type E/F - Schuko Female", "Power Type E/F - Schuko Male", "Powerstrip Type F - Schuko", "SFF Male", "SFP Male", "Power Type M - South Africa Male", "Speaker Raw Cable Male", "ST Male", "ST/UPC Male", "Power Type J - Switzerland Female", "Power Type J - Switzerland Male", "Thunderbolt Male", "TOSLINK Male", "Power Type G - UK Male", "Powerstrip Type G - UK", "Power Type A - USA Male", "Power Type B - USA Male", "USB A Female", "USB A Male", "USB B Female", "USB B Male", "USB C Female", "USB C Male", "USB Micro A Male", "USB Micro B Female", "USB Micro B Male", "USB Mini B Male", "VGA Female", "VGA Male", "XLR (3-pin) Female", "XLR (3-pin) Male"]
    url = 'https://stage-api.eetgroup.com/api/CableGuide/GetCableEndTypesA'
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

async def get_cable_ends_b(ctx: RunContext[AgentDependencies], cable_end_a: str) -> list[str]:
    print(f"calling the get_cable_ends_b with {cable_end_a}")
    url = f'https://stage-api.eetgroup.com/api/CableGuide/GetCableEndTypesB?cableEndTypeA={cable_end_a}'
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

def extract_order_id(query: str) -> str | None:
    """
    Extract order ID from natural language query.
    Primary format: Plain number sequences (e.g., "12345", "order 12345")
    Also supports: "#12345", "order #12345" (for flexibility)

    Returns: Order ID string or None if not found
    """
    patterns = [
        r'order\s*#?(\d+)',           # "order 12345" or "order #12345" (most common)
        r'#(\d+)',                    # "#12345" (alternative)
        r'\b(\d{4,})\b',              # standalone 4+ digit numbers (fallback)
    ]

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return match.group(1)

    return None

def translate_order_status(status_code: int) -> str:
    """
    Translate order status code to human-readable text.

    Args:
        status_code: Integer status code from order API

    Returns:
        Human-readable status string
    """
    status_map = {
        0: "Confirmed",
        1: "Picking in Progress",
        2: "Partly Dispatched",
        3: "Dispatched",
        10: "Received"
    }
    return status_map.get(status_code, f"Unknown Status ({status_code})")

def process_order_response(data: dict) -> dict:
    """
    Process raw order API response into clean structure for LLM.

    Translates status codes, formats dates, and extracts key information.

    Args:
        data: Raw response from order status API

    Returns:
        Processed order data with human-readable fields
    """
    processed = {
        "order_id": data.get("orderId"),
        "status": translate_order_status(data.get("status", -1)),
        "status_code": data.get("status"),
        "order_date": data.get("orderDate"),
        "shipping_agent": data.get("shippingAgentName"),
        "ship_to_address": data.get("shipToAddress"),
        "subtotal": data.get("subTotal"),
        "next_shipment": data.get("nextShipment"),
        "order_lines": []
    }

    # Process order lines if present
    if "orderLines" in data and data["orderLines"]:
        for line in data["orderLines"]:
            processed["order_lines"].append({
                "item_id": line.get("itemId"),
                "status": line.get("status")
            })

    # Add summary fields for quick reference
    processed["total_items"] = len(processed["order_lines"])

    return processed

async def search_product_info(ctx: RunContext[AgentDependencies], product_query: str) -> dict:
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

async def get_order_status(ctx: RunContext[AgentDependencies], user_query: str) -> dict:
    """
    Fetch order status from EET Order Status API.

    Extracts order ID from user_query. If no ID found, API returns latest order.

    Args:
        ctx: RunContext with dependencies (customer_id, language, erp_business_entity_id)
        user_query: Original user query for order ID extraction

    Returns:
        Processed order data dict with structure:
        {
            "order_id": str,               # Order identifier
            "status": str,                 # Human-readable: "Confirmed", "Picking in Progress",
                                          # "Partly Dispatched", "Dispatched", "Received"
            "status_code": int,            # Raw status code (0-10)
            "order_date": str,             # When order was placed (ISO format)
            "shipping_agent": str,         # Delivery company name
            "ship_to_address": str,        # Shipping address
            "subtotal": float,             # Order total amount
            "next_shipment": str | None,   # Next shipment date if available
            "order_lines": [               # Array of ordered items
                {
                    "item_id": str,        # Product identifier
                    "status": str | None   # Item-specific status
                }
            ],
            "total_items": int             # Count of items in order
        }

        Or error dict on failure:
        {
            "error": str,
            "message": str
        }
    """
    print(f"Calling get_order_status with query: {user_query}")

    # Extract order ID from query
    order_id = extract_order_id(user_query)
    if order_id:
        print(f"Extracted order ID: {order_id}")
    else:
        print("No order ID found, will fetch latest order")

    # Build API request
    url = "https://stage-api.eetgroup.com/api/AiSearch/OrderStatus"
    params = {
        "customerId": ctx.deps["customer_id"],
        "language": ctx.deps["language"],
        "erpBusinessEntityId": ctx.deps["erp_business_entity_id"],
    }
    if order_id:
        params["orderId"] = order_id

    # Call API with error handling
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            print(f"Raw order status response: {data}")

            # Process response to clean structure with translated status
            processed = process_order_response(data)
            print(f"Processed order data: {processed}")
            return processed

    except httpx.HTTPStatusError as e:
        error_msg = f"API error: {e.response.status_code}"
        if e.response.status_code == 404:
            error_msg += " - Order not found"
        print(error_msg)
        return {
            "error": error_msg,
            "message": "Could not fetch order status"
        }
    except httpx.TimeoutException:
        error_msg = "Order status API request timed out"
        print(error_msg)
        return {
            "error": "timeout",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return {
            "error": "unknown",
            "message": error_msg
        }

# Agent setup
model = OpenRouterModel(
    'mistralai/mistral-large-2512',
    provider=OpenRouterProvider(api_key=os.getenv('OPENROUTER_API_KEY')),
)
agent = Agent(
    model,
    deps_type=AgentDependencies,
    system_prompt="""READ THE WHOLE SYSTEM_PROMPT VERY CAREFULLY.

You are an AI agent that helps users with two main tasks:
1. Finding specific cables
2. Checking order status

You have four tools available:
- search_product_info(product_query): Search for product cable information
- get_cable_ends_a(): Get available cable connector types
- get_cable_ends_b(cable_end_a): Get compatible connector types
- get_order_status(user_query): Fetch order status information

=== STEP 1: QUERY CLASSIFICATION ===

Analyze the user query and classify it:

A) ORDER STATUS QUERY - If query contains:
   - Keywords: "order", "status", "delivery", "tracking", "shipment", "my order"
   - Order references: "order 12345", "12345", or any number sequence (4+ digits)
   - Status questions: "where is my order?", "when will it arrive?"

   ACTION: Use get_order_status(user_query) tool
   RESPONSE FORMAT: OrderStatusResponse with natural language summary

B) CABLE SEARCH QUERY - If query describes:
   - Cable types: "HDMI cable", "USB-C to HDMI"
   - Connectors: specific connector names
   - Product cables: "iPhone 15 cable", "MacBook charger"

   ACTION: Follow cable search flow (below)
   RESPONSE FORMAT: CableResponse with from_connector and to_connector

=== STEP 2: CABLE SEARCH FLOW (if classified as cable query) ===

Sub-step A: Decide if web search is needed
- If query mentions PRODUCT NAME (iPhone, MacBook, PS5):
  → Call search_product_info(product_query) first
- If query mentions cable DIRECTLY (HDMI to USB-C):
  → Skip search, proceed to cable lookup

Sub-step B: Cable lookup
1. Call get_cable_ends_a() to get all connector types
2. Select best match for FIRST connector from query/search results
3. Call get_cable_ends_b(cable_end_a) ONCE with selected connector
4. If no match found, return empty strings

Sub-step C: Return result
- Response type: "cable"
- Fill from_connector and to_connector fields
- If no match: use empty strings ""

=== STEP 3: ORDER STATUS FLOW (if classified as order query) ===

1. Call get_order_status(user_query)
   - Tool extracts order ID automatically from user_query
   - Tool fetches latest order if no ID found

2. Analyze the returned order data
   - Check for "error" field indicating API failure
   - The tool returns pre-processed data with:
     * status: Human-readable status (already translated from code)
     * order_id, order_date, shipping_agent, ship_to_address
     * subtotal, next_shipment, order_lines, total_items

3. Generate natural language summary including:
   - Order ID and status (use the "status" field, not "status_code")
   - When ordered (order_date) and current location/progress
   - Next shipment date if "next_shipment" is present
   - Shipping agent and delivery address
   - Number of items (total_items)
   - Handle errors gracefully with friendly messages

4. Return as OrderStatusResponse:
   - response_type: "order"
   - summary: your generated natural language text (2-3 sentences)
   - order_id: extracted ID or null

=== IMPORTANT RULES ===

1. For cable queries:
   - Never fabricate connector names
   - Only use connectors from get_cable_ends_a/b responses
   - Default to "male" connectors when gender is ambiguous
   - Call get_cable_ends_b ONLY ONCE

2. For order queries:
   - Always call get_order_status tool (pass full user_query as parameter)
   - Be conversational and concise in summaries
   - If API returns error, inform user politely

3. Response format:
   - ALWAYS set response_type correctly ("cable" or "order")
   - Match response structure to query type

=== EXAMPLES ===

Query: "What's the status of order 12345?"
Classification: ORDER STATUS
Action: get_order_status("What's the status of order 12345?")
Response: OrderStatusResponse(
    response_type="order",
    summary="Order 12345 (placed on Dec 5th) is currently Dispatched with 3 items. DHL is handling delivery to your address. Expected next shipment: December 15th.",
    order_id="12345"
)

Query: "HDMI to USB-C cable"
Classification: CABLE SEARCH
Action: Cable lookup flow
Response: CableResponse(
    response_type="cable",
    from_connector="HDMI Male",
    to_connector="USB C Male"
)

Query: "Where is my order?"
Classification: ORDER STATUS
Action: get_order_status("Where is my order?")
Response: OrderStatusResponse(
    response_type="order",
    summary="Your most recent order (12340) was delivered on December 8th, 2025.",
    order_id="12340"
)

Query: "Check order 67890"
Classification: ORDER STATUS
Action: get_order_status("Check order 67890")
Response: OrderStatusResponse(
    response_type="order",
    summary="Order 67890 is Confirmed and currently being picked. You have 5 items ordered on Dec 9th. Shipment expected by December 12th via FedEx.",
    order_id="67890"
)

Query: "iPhone 15 charging cable"
Classification: CABLE SEARCH (with product search)
Action: search_product_info → cable lookup flow
Response: CableResponse(
    response_type="cable",
    from_connector="USB C Male",
    to_connector="Lightning Male"
)
""",
    output_type=AgentResponse,
)

# Add tools
agent.tool(get_cable_ends_a)
agent.tool(get_cable_ends_b)
agent.tool(search_product_info)
agent.tool(get_order_status)

@app.get("/search")
async def search(
    query: str,
    customerId: str,
    language: str,
    erpBusinessEntityId: int
):
    """
    Universal search endpoint for cable queries and order status.

    Args:
        query: Natural language query (cable or order related)
        customerId: Customer ID for order lookup
        language: Language code (e.g., 'en-US', 'en-GB')
        erpBusinessEntityId: Business entity ID for API routing

    Returns:
        CableResponse (for cable queries) or OrderStatusResponse (for orders)
    """
    # Create dependencies to pass to agent
    deps = AgentDependencies(
        customer_id=customerId,
        language=language,
        erp_business_entity_id=erpBusinessEntityId
    )

    # Run agent with dependencies
    result = await agent.run(query, deps=deps)

    # Return the discriminated union output
    return result.output
