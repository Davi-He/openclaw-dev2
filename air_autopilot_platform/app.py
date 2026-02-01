"""
空中自动驾驶大数据平台 - 主应用
整合所有模块的统一入口
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os

# 导入各个模块
from api.main import app as api_app
from data_processing.realtime_processor import RealTimeProcessor, DataPoint, DataType
from ml_models.flight_prediction import FlightPathPredictor, SafetyAnalyzer
from visualization.map_visualizer import MapVisualizer, DashboardGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlatformManager:
    """
    平台管理器
    负责协调各个子系统
    """
    
    def __init__(self):
        self.realtime_processor = RealTimeProcessor()
        self.ml_predictor = FlightPathPredictor()
        self.safety_analyzer = SafetyAnalyzer()
        self.map_visualizer = MapVisualizer()
        self.dashboard_generator = DashboardGenerator()
        
        # 数据存储
        self.flight_data_store = {}
        self.prediction_cache = {}
        self.safety_reports = {}
        
    async def initialize(self):
        """初始化平台各组件"""
        logger.info("正在初始化空中自动驾驶大数据平台...")
        
        # 启动实时处理器
        await self.realtime_processor.start()
        
        logger.info("平台初始化完成")
    
    async def shutdown(self):
        """关闭平台"""
        logger.info("正在关闭平台...")
        await self.realtime_processor.stop()
        logger.info("平台已关闭")

# 创建全局平台实例
platform_manager = PlatformManager()

# 创建主应用
main_app = FastAPI(
    title="空中自动驾驶大数据平台",
    description="综合性的空中自动驾驶大数据处理平台",
    version="1.0.0"
)

# 添加CORS中间件
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加API路由
main_app.include_router(api_app.router, prefix="/api/v1", tags=["api"])

# 自定义数据模型
class FlightDataRequest(BaseModel):
    flight_id: str
    data: Dict
    data_type: str

class PredictionRequest(BaseModel):
    flight_id: str
    current_state: Dict
    steps: int = 10

class SafetyCheckRequest(BaseModel):
    flight_id: str
    predicted_trajectory: List[Dict]
    obstacles: List[Dict] = []

# 自定义API端点
@main_app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    await platform_manager.initialize()

@main_app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    await platform_manager.shutdown()

@main_app.get("/")
async def root():
    """根路径"""
    return {
        "message": "空中自动驾驶大数据平台",
        "version": "1.0.0",
        "modules": [
            "Real-time Data Processing",
            "Machine Learning Prediction", 
            "Safety Analysis",
            "Visualization Dashboard",
            "API Services"
        ],
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@main_app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "components": {
            "realtime_processor": "running",
            "ml_predictor": "loaded" if platform_manager.ml_predictor.is_trained else "not trained",
            "safety_analyzer": "ready",
            "visualizer": "ready"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@main_app.post("/data/process")
async def process_flight_data(request: FlightDataRequest):
    """处理飞行数据"""
    try:
        # 创建数据点
        data_point = DataPoint(
            flight_id=request.flight_id,
            data_type=DataType[request.data_type.upper()] if request.data_type.upper() in DataType.__members__ else DataType.TELEMETRY,
            timestamp=datetime.utcnow(),
            data=request.data
        )
        
        # 添加到实时处理器
        await platform_manager.realtime_processor.add_data(data_point)
        
        # 存储数据
        if request.flight_id not in platform_manager.flight_data_store:
            platform_manager.flight_data_store[request.flight_id] = []
        
        platform_manager.flight_data_store[request.flight_id].append({
            "timestamp": data_point.timestamp.isoformat(),
            "data": data_point.data,
            "data_type": data_point.data_type.value
        })
        
        return {
            "status": "processed",
            "flight_id": request.flight_id,
            "data_type": request.data_type,
            "timestamp": data_point.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing flight data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@main_app.post("/ml/predict")
async def predict_flight_path(request: PredictionRequest):
    """预测飞行路径"""
    try:
        # 检查模型是否已训练
        if not platform_manager.ml_predictor.is_trained:
            # 如果没有训练数据，使用模拟数据训练一个简单模型
            logger.info("No trained model found, training with sample data...")
            sample_data = [[{
                'latitude': request.current_state.get('latitude', 39.9042),
                'longitude': request.current_state.get('longitude', 116.4074),
                'altitude': request.current_state.get('altitude', 100),
                'speed': request.current_state.get('speed', 50),
                'heading': request.current_state.get('heading', 0),
                'battery_level': request.current_state.get('battery_level', 80),
                'wind_speed': request.current_state.get('wind_speed', 5),
                'wind_direction': request.current_state.get('wind_direction', 90),
                'temperature': request.current_state.get('temperature', 25),
                'humidity': request.current_state.get('humidity', 50),
                'pressure': request.current_state.get('pressure', 1013),
                'timestamp': datetime.utcnow().isoformat()
            }]]
            platform_manager.ml_predictor.train(sample_data)
        
        # 进行预测
        predicted_trajectory = platform_manager.ml_predictor.predict_trajectory(
            request.current_state, 
            steps=request.steps
        )
        
        # 缓存预测结果
        cache_key = f"{request.flight_id}_{datetime.utcnow().timestamp()}"
        platform_manager.prediction_cache[cache_key] = {
            "flight_id": request.flight_id,
            "prediction_time": datetime.utcnow().isoformat(),
            "trajectory": predicted_trajectory
        }
        
        return {
            "flight_id": request.flight_id,
            "predicted_trajectory": predicted_trajectory,
            "steps": request.steps,
            "prediction_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error predicting flight path: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@main_app.post("/safety/check")
async def check_flight_safety(request: SafetyCheckRequest):
    """检查飞行安全"""
    try:
        # 进行安全分析
        safety_result = platform_manager.safety_analyzer.analyze_safety(
            request.predicted_trajectory,
            obstacles=request.obstacles
        )
        
        # 存储安全报告
        report_id = f"safety_{request.flight_id}_{datetime.utcnow().timestamp()}"
        platform_manager.safety_reports[report_id] = {
            "flight_id": request.flight_id,
            "safety_result": safety_result,
            "check_time": datetime.utcnow().isoformat()
        }
        
        return {
            "flight_id": request.flight_id,
            "safety_report": safety_result,
            "report_id": report_id
        }
    except Exception as e:
        logger.error(f"Error checking flight safety: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@main_app.get("/dashboard/generate")
async def generate_dashboard():
    """生成可视化仪表板"""
    try:
        # 使用存储的飞行数据生成仪表板
        dashboard_html = platform_manager.dashboard_generator.generate_dashboard(
            flights_data=platform_manager.flight_data_store,
            predicted_trajectories={},
            obstacles=[],
            no_fly_zones=[]
        )
        
        return {
            "dashboard_html_generated": True,
            "timestamp": datetime.utcnow().isoformat(),
            "flight_count": len(platform_manager.flight_data_store)
        }
    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@main_app.get("/data/summary")
async def get_data_summary():
    """获取数据摘要"""
    total_flights = len(platform_manager.flight_data_store)
    total_data_points = sum(len(data) for data in platform_manager.flight_data_store.values())
    prediction_count = len(platform_manager.prediction_cache)
    safety_report_count = len(platform_manager.safety_reports)
    
    recent_flights = []
    for flight_id, data_list in platform_manager.flight_data_store.items():
        if data_list:
            recent_data = data_list[-1]
            recent_flights.append({
                "flight_id": flight_id,
                "last_update": recent_data["timestamp"],
                "data_points": len(data_list),
                "last_position": {
                    "latitude": recent_data["data"].get("latitude"),
                    "longitude": recent_data["data"].get("longitude"),
                    "altitude": recent_data["data"].get("altitude")
                }
            })
    
    return {
        "summary": {
            "total_flights": total_flights,
            "total_data_points": total_data_points,
            "prediction_count": prediction_count,
            "safety_report_count": safety_report_count,
            "active_components": [
                "realtime_processor",
                "ml_predictor",
                "safety_analyzer",
                "visualizer"
            ]
        },
        "recent_flights": recent_flights[:10]  # 最近10个航班
    }

# 为了兼容直接运行，我们将API应用挂载到主应用下
app = main_app

if __name__ == "__main__":
    # 运行应用
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )