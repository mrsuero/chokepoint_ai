# ChokePoint AI

ChokePoint AI is a computer-vision demo system with a Python backend and a React/Vite frontend. The backend analyzes video frames with YOLO, writes live telemetry into the frontend `public/` folder, and the UI renders the current feed and metrics.

## Project Structure

- `backend_ai/`: Python vision pipelines and helper scripts
- `frontend_ui/`: React dashboard built with Vite and Tailwind
- `requirements.txt`: Python dependencies for the backend

## Requirements

- Python 3.10+ recommended
- Node.js 18+ recommended
- `pip` and `npm`

## Setup

### 1. Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend

```bash
cd frontend_ui
npm install
```

## Run

### Backend

Run the main pipeline from the backend folder:

```bash
cd backend_ai
python main_pipeline4.py
```

If the configured video source is missing, the backend falls back to simulation mode and still updates the frontend telemetry files.

### Frontend

```bash
cd frontend_ui
npm run dev
```

Open the local Vite URL shown in the terminal.

## Makefile Targets

If `make` is available in your shell, the root Makefile provides common commands:

- `make help`
- `make setup-backend`
- `make setup-frontend`
- `make run-backend`
- `make run-frontend`

## Notes

- The frontend reads live data from `frontend_ui/public/chokepoint_metrics.json` and frame images from the same folder.
- Default demo login credentials in the UI are `admin/admin123` and `operator/op123`.
- The backend scripts `main_pipeline1.py` to `main_pipeline4.py` are available if you want to switch pipelines later.