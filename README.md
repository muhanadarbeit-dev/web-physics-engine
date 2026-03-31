# Web Physics Engine 🚀

A high-performance, custom-built 2D rigid-body physics simulation engine with a complete separation of concerns. The core physics logic runs on a Python FastAPI backend, calculating collisions at 60 FPS, while a beautiful, glassmorphic HTML5 Canvas frontend renders the simulation in real-time via WebSockets.

## Features
- **Custom Physics Engine:** Features broad-phase and SAT narrow-phase collision detection, impulse-based resolution, and positional correction.
- **WebSocket Streaming:** Telemetry, kinematics, and body coordinates stream live to clients.
- **Web Parity with Desktop:** Fully replicates the PyQt desktop experience in the browser, featuring adjustable gravity, elastic toggles, polygons spanning up to 25 edges, and real-time kinetic energy/momentum graphing.
- **Dynamic Density Rendering:** Assigns rainbow gradients to bodies dynamically based on mass density.
- **Interactive UI:** Play/pause, reset, customize, and spawn interactive physics bodies on-the-fly.

## Build Requirements
- Python 3.9+
- `fastapi`
- `uvicorn`
- `websockets`

## How to Run Local Server
1. Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```
2. Start the Uvicorn ASGI server:
```bash
python -m uvicorn src_web.server:app --host 0.0.0.0 --port 8000
```
3. Open your browser and navigate to `http://localhost:8000`.
