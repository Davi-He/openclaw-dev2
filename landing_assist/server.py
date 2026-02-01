"""
空中自动驾驶辅助降落系统服务器
提供API接口支持
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List
import asyncio
import json
from datetime import datetime

app = FastAPI(title="空中自动驾驶辅助降落系统 API", version="1.0.0")

# 模拟飞行器状态
class FlightStatus:
    def __init__(self):
        self.altitude = 120.0  # 高度(米)
        self.speed = 5.2       # 速度(m/s)
        self.battery = 85      # 电池(%)
        self.latitude = 39.9042  # 纬度
        self.longitude = 116.4074  # 经度
        self.status = "飞行中"  # 状态
        self.landing_target = None  # 降落目标
        self.is_landing = False    # 是否在降落
        self.is_manual_mode = False  # 是否手动模式

flight_status = FlightStatus()

class LandingTarget(BaseModel):
    x: float
    y: float
    latitude: float = None
    longitude: float = None

class LandingRequest(BaseModel):
    target: LandingTarget
    mode: str = "precision"  # precision, emergency

@app.get("/")
async def read_root():
    return {"message": "空中自动驾驶辅助降落系统 API", "version": "1.0.0"}

@app.get("/api/status")
async def get_flight_status():
    """获取飞行器状态"""
    return {
        "altitude": flight_status.altitude,
        "speed": flight_status.speed,
        "battery": flight_status.battery,
        "latitude": flight_status.latitude,
        "longitude": flight_status.longitude,
        "status": flight_status.status,
        "landing_target": flight_status.landing_target,
        "is_landing": flight_status.is_landing,
        "is_manual_mode": flight_status.is_manual_mode,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/landing/target")
async def set_landing_target(target: LandingTarget):
    """设置降落目标"""
    flight_status.landing_target = target.dict()
    return {"message": "降落目标已设置", "target": target.dict()}

@app.post("/api/landing/start")
async def start_landing(request: LandingRequest):
    """开始降落"""
    if flight_status.is_landing:
        return {"error": "正在降落中"}
    
    flight_status.is_landing = True
    flight_status.status = "自动降落中"
    flight_status.landing_target = request.target.dict()
    
    # 模拟降落过程
    async def simulate_landing():
        steps = 100
        for i in range(steps):
            if not flight_status.is_landing:
                break
            await asyncio.sleep(0.1)
            # 模拟高度下降
            flight_status.altitude = max(0, flight_status.altitude - 1.2)
            flight_status.speed = max(0, flight_status.speed - 0.05)
        
        if flight_status.is_landing:
            flight_status.status = "已降落"
            flight_status.altitude = 0
            flight_status.speed = 0
            flight_status.is_landing = False
    
    # 在后台运行降落模拟
    asyncio.create_task(simulate_landing())
    
    return {"message": "开始自动降落", "target": request.target.dict(), "mode": request.mode}

@app.post("/api/landing/cancel")
async def cancel_landing():
    """取消降落"""
    if not flight_status.is_landing:
        return {"error": "未在降落状态"}
    
    flight_status.is_landing = False
    flight_status.status = "飞行中"
    
    return {"message": "降落已取消"}

@app.post("/api/control/takeoff")
async def takeoff():
    """起飞"""
    if flight_status.is_landing:
        return {"error": "正在降落，无法起飞"}
    
    flight_status.status = "起飞中"
    
    # 模拟起飞
    await asyncio.sleep(2)
    flight_status.altitude = 120.0
    flight_status.speed = 5.2
    flight_status.status = "飞行中"
    
    return {"message": "起飞完成", "altitude": flight_status.altitude}

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """实时遥测数据WebSocket"""
    await websocket.accept()
    try:
        while True:
            # 发送实时遥测数据
            data = {
                "altitude": flight_status.altitude,
                "speed": flight_status.speed,
                "battery": flight_status.battery,
                "latitude": flight_status.latitude,
                "longitude": flight_status.longitude,
                "status": flight_status.status,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(0.5)  # 每0.5秒发送一次
    except WebSocketDisconnect:
        print("WebSocket disconnected")

# 挂载静态文件
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)