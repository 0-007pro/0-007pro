import base64
import os
from flask import Flask, Response, jsonify, request
import httpx

app = Flask(__name__)

XIAOMI_BASE_URL = os.getenv("XIAOMI_BASE_URL", "https://api.xiaomimimo.com")
XIAOMI_API_KEY = os.getenv("XIAOMI_API_KEY", "")
DEFAULT_MODEL = os.getenv("XIAOMI_MODEL", "mimo-v2.5-tts")
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "茉莉")
PORT = int(os.getenv("PORT", "8080"))

VOICE_MAP = {
    "alloy": "茉莉",
    "echo": "茉莉",
    "fable": "茉莉",
    "nova": "茉莉",
    "onyx": "茉莉",
    "shimmer": "茉莉",
}

DEFAULT_STYLE_PROMPT = (
    "请用自然、清晰、情绪稳定的中文女声朗读，语速中等，停顿自然。"
)


def resolve_api_key() -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return XIAOMI_API_KEY


def resolve_model(body: dict) -> str:
    model = body.get("model")
    if model and model != "tts-1":
        return model
    return DEFAULT_MODEL


@app.get("/v1/models")
def list_models():
    return jsonify(
        {
            "object": "list",
            "data": [
                {"id": "tts-1", "object": "model", "owned_by": "proxy"},
                {"id": "mimo-v2.5-tts", "object": "model", "owned_by": "xiaomi"},
                {
                    "id": "mimo-v2.5-tts-voicedesign",
                    "object": "model",
                    "owned_by": "xiaomi",
                },
                {
                    "id": "mimo-v2.5-tts-voiceclone",
                    "object": "model",
                    "owned_by": "xiaomi",
                },
            ],
        }
    )


@app.post("/v1")
@app.post("/v1/audio/speech")
def tts():
    body = request.get_json(force=True, silent=True) or {}

    text = body.get("input", "")
    if not text:
        return jsonify({"error": "Missing input text"}), 400

    voice = body.get("voice", "alloy")
    mapped_voice = VOICE_MAP.get(voice, voice or DEFAULT_VOICE)

    model = resolve_model(body)
    style_prompt = body.get("instructions") or DEFAULT_STYLE_PROMPT

    requested_fmt = body.get("response_format", "mp3")
    xiaomi_fmt = "wav" if requested_fmt not in ("wav", "mp3") else requested_fmt

    api_key = resolve_api_key()
    if not api_key:
        return jsonify({"error": "Missing API key"}), 401

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": style_prompt},
            {"role": "assistant", "content": text},
        ],
        "audio": {
            "format": xiaomi_fmt,
            "voice": mapped_voice,
        },
    }

    try:
        resp = httpx.post(
            f"{XIAOMI_BASE_URL}/v1/chat/completions",
            headers={"api-key": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=httpx.Timeout(180.0, connect=30.0),
        )
    except httpx.ReadTimeout:
        return jsonify({"error": "Upstream Xiaomi TTS timeout"}), 504

    if resp.status_code >= 400:
        return Response(resp.text, status=resp.status_code, content_type="application/json")

    data = resp.json()
    try:
        b64_audio = data["choices"][0]["message"]["audio"]["data"]
    except (KeyError, IndexError, TypeError):
        return jsonify({"error": "Unexpected Xiaomi response", "raw": data}), 502

    audio_bytes = base64.b64decode(b64_audio)
    content_type = "audio/wav" if xiaomi_fmt == "wav" else "audio/mpeg"
    return Response(audio_bytes, content_type=content_type)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
