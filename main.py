import os
import httpx
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="XiaoZhi VK Music")

VK_TOKEN = os.getenv("VK_ACCESS_TOKEN", "")
VK_VERSION = "5.199"


@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "XiaoZhi VK Music"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "vk_token_configured": bool(VK_TOKEN)
    }


@app.get("/search")
async def search(q: str = Query(..., min_length=1, max_length=200)):
    if not VK_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="VK_ACCESS_TOKEN is not configured"
        )

    params = {
        "access_token": VK_TOKEN,
        "v": VK_VERSION,
        "q": q,
        "count": 10
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                "https://api.vk.com/method/audio.search",
                params=params
            )
            response.raise_for_status()
            data = response.json()

        if "error" in data:
            raise HTTPException(
                status_code=502,
                detail=data["error"].get("error_msg", "VK API error")
            )

        result = data.get("response", {})
        tracks = result.get("items", []) if isinstance(result, dict) else []

        return {
            "query": q,
            "tracks": [
                {
                    "id": t.get("id"),
                    "owner_id": t.get("owner_id"),
                    "artist": t.get("artist"),
                    "title": t.get("title"),
                    "duration": t.get("duration")
                }
                for t in tracks
            ]
        }

    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to VK API"
        )
