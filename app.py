from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
import json
import httpx
import os

app = FastAPI()

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

# Agent setup
model = OpenRouterModel(
    'mistralai/mistral-large-2512',
    provider=OpenRouterProvider(api_key=os.getenv('OPENROUTER_API_KEY')),
)
agent = Agent(
    model,
    system_prompt="READ THE WHOLE SYSTEM_PROMPT VERY CAREFULLY. You are an agent that has to figure out based on the giving query, if a user is searching for a specific cable. You have to be certain that the cable actually exist. The user might use conversational speech to decribe the cable they are looking for. You have to pick out 2 cable ends from the sentence - if gender isn't provided assume it's male where it makes sense. To verify that this cable exist use the 'get_cable_ends_a' tool. This returns a list of available cable ends. Pick one based on the FIRST cable-end you see from the query. Then use 'get_cable_ends_b' ONCE and ONLY once! along with the best match from 'get_cable_ends_a' to find the other end of the cable based on the query - DO NOT CALL get_cable_ends_b more than once. If you cannot find a match from get_cable_ends_b, this is a clear sign that the cable combination doesn't exist - please tell the user. Do not make up any cable ends. If you cannot find a match return empty strings.",
    output_type=CableQuery,
)

# Add tools
agent.tool(get_cable_ends_a)
agent.tool(get_cable_ends_b)

@app.get("/search")
async def search(query: str):
    result = await agent.run(query)
    return result.output
