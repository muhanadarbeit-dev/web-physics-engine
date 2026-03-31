import asyncio
import json
import math
import random
import os
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .physics.ball import Ball
from .physics.engine import PhysicsEngine
from .physics.polygon import PolygonBody

app = FastAPI()

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

engine = PhysicsEngine()
engine.set_world_size(1000, 550)
connected_clients: List[WebSocket] = []
is_running = True

def density_to_rgb(density: float):
    import colorsys
    min_d, max_d = 0.1, 10.0
    val = max(0.0, min(1.0, (density - min_d) / (max_d - min_d)))
    
    # قوس المطر: الأزرق للكثافة المنخفضة والأحمر للكثافة العالية
    # الأزرق = 240 درجة، الأحمر = 0 درجة
    hue = (240.0 - val * 240.0) / 360.0
    
    # HLS to RGB (Hue, Lightness=0.6, Saturation=0.9 for vibrant colors)
    r, g, b = colorsys.hls_to_rgb(hue, 0.6, 0.9)
    return (int(r * 255), int(g * 255), int(b * 255))

def spawn_ball(radius=None, density=None, speed=None, x=None, y=None):
    r = radius if radius is not None else random.uniform(5.0, 50.0)
    d = density if density is not None else random.uniform(0.1, 10.0)
    xx = x if x is not None else random.uniform(r + 4, engine.world_width - r - 4)
    yy = y if y is not None else random.uniform(r + 4, engine.world_height - r - 4)
    ball = Ball(xx, yy, r, density=d, restitution=0.72, fill_rgb=density_to_rgb(d))
    
    actual_speed = speed if speed is not None else random.uniform(50.0, 150.0)
    ang = random.uniform(0, 2 * math.pi)
    ball.vx = actual_speed * math.cos(ang)
    ball.vy = actual_speed * math.sin(ang)
    ball.angular_velocity = random.uniform(-4.0, 4.0)
    engine.add_body(ball)

def spawn_polygon(radius=None, density=None, speed=None, edges=None, x=None, y=None):
    rad = radius if radius is not None else random.uniform(5.0, 50.0)
    d = density if density is not None else random.uniform(0.1, 10.0)
    xx = x if x is not None else random.uniform(rad + 4, engine.world_width - rad - 4)
    yy = y if y is not None else random.uniform(rad + 4, engine.world_height - rad - 4)
    
    n_e = edges if edges is not None else random.randint(3, 8)
    
    poly = PolygonBody(xx, yy, rad, density=d, restitution=0.65, fill_rgb=density_to_rgb(d), num_edges=n_e)
    actual_speed = speed if speed is not None else random.uniform(50.0, 150.0)
    ang = random.uniform(0, 2 * math.pi)
    poly.vx = actual_speed * math.cos(ang)
    poly.vy = actual_speed * math.sin(ang)
    poly.angular_velocity = random.uniform(-3.5, 3.5)
    poly.angle = random.uniform(0.0, 2.0 * math.pi)
    engine.add_body(poly)

for _ in range(3): spawn_ball()
for _ in range(3):spawn_polygon()

@app.get("/")
async def get_index():
    return FileResponse(os.path.join(static_path, "index.html"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global is_running
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                cmd = msg.get("action")
                
                rad = msg.get("radius")
                den = msg.get("density")
                spd = msg.get("speed")
                edges = msg.get("edges")
                
                if cmd == "add_ball":
                    spawn_ball(radius=rad, density=den, speed=spd)
                elif cmd == "add_poly":
                    spawn_polygon(radius=rad, density=den, speed=spd, edges=edges)
                elif cmd == "clear":
                    engine.clear()
                elif cmd == "toggle_play":
                    is_running = not is_running
                elif cmd == "set_gravity":
                    if "down" in msg: engine.gravity_down = msg["down"]
                    if "up" in msg: engine.gravity_up = msg["up"]
                    if "left" in msg: engine.gravity_left = msg["left"]
                    if "right" in msg: engine.gravity_right = msg["right"]
                elif cmd == "set_elastic":
                    if "elastic" in msg: engine.elastic_collisions = msg["elastic"]

            except Exception as e:
                print("Error parsing msg:", e)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def simulation_loop():
    dt = 1.0 / 60.0
    while True:
        if is_running:
            engine.step(dt)
        
        state = {
            "telemetry": {
                "ke": engine.total_kinetic_energy(),
                "px": engine.total_linear_momentum()[0],
                "py": engine.total_linear_momentum()[1],
                "pmag": engine.scalar_momentum()
            },
            "bodies": []
        }
        
        for b in engine.bodies:
            rb, gb, bb = b.fill_rgb
            item = {
                "x": b.x, "y": b.y, "angle": b.angle,
                "color": f"rgb({rb},{gb},{bb})"
            }
            if isinstance(b, Ball):
                item["type"] = "ball"
                item["radius"] = b.radius
            elif isinstance(b, PolygonBody):
                item["type"] = "polygon"
                item["verts"] = [(v[0] - b.x, v[1] - b.y) for v in b.get_world_vertices()]
            state["bodies"].append(item)
            
        json_state = json.dumps(state)
        
        for client in connected_clients:
            try:
                await client.send_text(json_state)
            except:
                pass
                
        await asyncio.sleep(dt)

@app.on_event("startup")
async def start_sim():
    asyncio.create_task(simulation_loop())

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    # إزالة reload=True لأنها غير مناسبة ببيئة الإنتاج (Production)
    uvicorn.run("src_web.server:app", host="0.0.0.0", port=port)
