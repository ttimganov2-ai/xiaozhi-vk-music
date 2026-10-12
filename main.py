import os
import httpx
from fastapi import FastAPI, HTTPException, Query
from importlib.metadata import version

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

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            response = await client.get(
                "https://api.vk.com/method/audio.search",
                params=params
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError:
            raise HTTPException(
                status_code=502,
                detail="Could not connect to VK API"
            )

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
                "id": track.get("id"),
                "owner_id": track.get("owner_id"),
                "artist": track.get("artist"),
                "title": track.get("title"),
                "duration": track.get("duration")
            }
            for track in tracks
        ]
    }
@app.get("/vk-status")
async def vk_status():
    try:
        return {
            "vk_api_installed": True,
            "vk_api_version": version("vk_api"),
            "message": "Library is ready"
        }
    except Exception:
        return {
            "vk_api_installed": False,
            "message": "Library is not installed"
        }

from fastapi.responses import HTMLResponse

VK_ID_APP_ID = os.getenv("VK_ID_APP_ID", "")


@app.get("/login", response_class=HTMLResponse)
async def login():
    if not VK_ID_APP_ID:
        raise HTTPException(
            status_code=503,
            detail="VK_ID_APP_ID is not configured"
        )

    return HTMLResponse("""
<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>XiaoZhi VK Music</title>
    <script src="https://unpkg.com/@vkid/sdk@2.6.9/dist-sdk/umd/index.js"></script>

</head>
<body style="font-family:Arial,sans-serif;text-align:center;padding:30px">
    <h2>XiaoZhi VK Music</h2>
    <p>Войди через VK ID, чтобы продолжить.</p>
    <button id="vk_auth_button"
        style="background:#0077ff;color:white;border:0;border-radius:8px;padding:14px 24px;font-size:17px">
        Войти через VK
    </button>
    <p id="message"></p>

    <script>
    const APP_ID = 54813775;
    const REDIRECT_URL =
      "https://xiaozhi-vk-music-production.up.railway.app/auth/callback";

    function randomString(length) {
        const chars =
          "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";
        const bytes = crypto.getRandomValues(new Uint8Array(length));
        return Array.from(bytes, b => chars[b % chars.length]).join("");
    }

    const state = randomString(32);
    const codeVerifier = randomString(64);

    document.getElementById("vk_auth_button").onclick = async function () {
        try {
            sessionStorage.setItem("vk_state", state);
            sessionStorage.setItem("vk_code_verifier", codeVerifier);

            VKID.Config.init({
                app: APP_ID,
                redirectUrl: REDIRECT_URL,
                state: state,
                codeVerifier: codeVerifier,
                scope: "email"
            });

            await VKID.Auth.login();
        } catch (error) {
    const message = error instanceof Error
        ? error.message
        : String(error);

    document.getElementById("message").textContent =
        "Ошибка авторизации: " + message;

    console.error(error);
}
    };
    </script>
</body>
</html>
    """)
