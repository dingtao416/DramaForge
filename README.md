# DramaForge v2.0

AI-powered short drama video generation platform.

> From a single idea to complete short drama videos, automated in three steps.

## Project Structure

- `dramaForge_bac/` - Backend (Python + FastAPI)
- `dramaForge_web/` - Frontend (Vue 3 + TypeScript + Vite)
- `docs/` - Technical documentation

## Core Workflow

Step 1: Script -> Step 2: Assets (Characters + Scenes) -> Step 3: Episode Videos

## Tech Stack

- Backend: Python 3.11, FastAPI, SQLAlchemy 2.0, ARQ
- Frontend: Vue 3, TypeScript, Vite, TailwindCSS, Pinia
- AI Hub: laozhang.ai (GPT-4o, sora-image, tts-1, veo-3.1)

## Quick Start

### Backend
cd dramaForge_bac
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

### Frontend
cd dramaForge_web
npm install
npm run dev

## License

MIT
