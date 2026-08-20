# Chinese → Khmer Video AI — Full Deploy

Mobile-first web app for iPhone:
Chinese video → Chinese transcription → Khmer summary → timed Khmer voice-over → Khmer subtitles → MP4.

## Stack
- FastAPI
- FFmpeg + libass
- OpenAI API
- Docker
- Render-compatible deployment

## 1. Create your OpenAI API key
Create an API key in the OpenAI Platform and keep it secret. Do NOT put it in frontend JavaScript or commit it to GitHub.

## 2. Local/Docker test
Copy `.env.example` to `.env` and set:
OPENAI_API_KEY=...

Then:
```bash
docker compose up --build
```
Open:
http://localhost:8000

## 3. Deploy to Render
Render supports deploying a Web Service from a GitHub repo and supports Dockerfiles. In Render:
- New → Web Service
- Connect your GitHub repository
- Runtime/Language: Docker
- Dockerfile: `Dockerfile`
- Add environment variable `OPENAI_API_KEY`
- Deploy

Render gives the service an `onrender.com` URL. Free web services may spin down after inactivity.

## 4. iPhone
Open the Render URL in Safari → Share → Add to Home Screen.

## Notes
- The app generates an AI narrator voice; it does not clone a real person's voice.
- Long videos require more server RAM/CPU and may exceed platform request/time limits. For production, move processing to a background worker/queue and object storage.
- Generated files are stored on the container filesystem in this MVP. Use persistent/object storage for production.
