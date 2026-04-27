# PS-5 Challenge Project

This repository contains a benchmark challenge with backend and frontend modules, plus a private `resources` pack used for controlled evaluation.

## Project folders
- `backend/` - Flask API and engine implementations.
- `frontend/` - React UI for running benchmarks.
- `resources/` - challenge reports and support materials (kept private via `.gitignore`).

## Run backend
1. Open terminal in `backend`.
2. Install requirements (if needed): `pip install flask flask-cors psutil`.
3. Start server: `python app.py`.

## Run frontend
1. Open terminal in `frontend`.
2. Install dependencies: `npm install`.
3. Start app: `npm run dev`.

## Privacy and leak protection
- `.gitignore` is configured to exclude private challenge resource files.
- Solution-style backend folder `backend/engine_optimized/` is ignored.
- Local analysis/debug artifacts are ignored.
