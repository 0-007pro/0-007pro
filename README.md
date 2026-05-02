# Xiaomi TTS OpenAI-Compatible Proxy (for SillyTavern)

This proxy lets SillyTavern call Xiaomi MiMo TTS through OpenAI-compatible endpoints.

## Features
- Supports both `POST /v1` and `POST /v1/audio/speech`.
- Allows model selection directly from SillyTavern by setting `model` to:
  - `mimo-v2.5-tts`
  - `mimo-v2.5-tts-voicedesign`
  - `mimo-v2.5-tts-voiceclone`
- Passes SillyTavern `instructions` to Xiaomi as style prompt.
- Provides a default style prompt if `instructions` is not sent.

## Run
```bash
pip install -r requirements.txt
export XIAOMI_API_KEY='your_key'
export XIAOMI_MODEL='mimo-v2.5-tts'   # fallback if ST sends tts-1
export DEFAULT_VOICE='茉莉'
export PORT=8080
python mini_proxy.py
```

## SillyTavern settings
- Provider: OpenAI Compatible
- Endpoint: `http://127.0.0.1:8080/v1`
- Model: `mimo-v2.5-tts-voicedesign` (or any supported model)
- Voice: `alloy` (mapped to `茉莉` by default) or direct Xiaomi voice name.

## Notes
- If ST sends `model: tts-1`, proxy falls back to `XIAOMI_MODEL`.
- Timeout is set to 180 seconds for long text.
