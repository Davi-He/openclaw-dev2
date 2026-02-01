"""
实时数据处理器
处理来自飞行器的实时数据流
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DataType(Enum):
    TELEMETRY = "telemetry"
    SENSOR = "sensor"
    CAMERA = "camera"
    LIDAR = "lidar"
    GPS = "gps"

@dataclass
class DataPoint:
    """数据点结构"""
    flight_id: str
    data_type: DataType
    timestamp: datetime
    data: Dict[str, Any]
    source: str = ""

class RealTimeProcessor:
    """实时数据处理器"""
    
    def __init__(self):
        self.data_buffer: Dict[str, List[DataPoint]] = {}
        self.processing_queue = asyncio.Queue()
        self.is_running = False
        
        # 数据验证规则
        self.validation_rules = {
            'latitude': {'min': -90, 'max': 90},
            'longitude': {'min': -180, 'max': 180},
            'altitude': {'min': 0, 'max': 10000},  # 最大10km
            'speed': {'min': 0, 'max': 300},  # 最大300 km/h
            'battery_level': {'min': 0, 'max': 100}
        }
        
        # 异常检测阈值
        self.anomaly_thresholds = {
            'position_drift': 0.01,  # 位置漂移阈值
            'speed_change': 50,      # 速度变化阈值 (km/h)
            'altitude_change': 100   # 高度变化阈值 (m)
        }

    async def start(self):
        """启动处理器"""
        self.is_running = True
        logger.info("Real-time processor started")
        # 启动处理任务
        asyncio.create_task(self._processing_loop())

    async def stop(self):
        """停止处理器"""
        self.is_running = False
        logger.info("Real-time processor stopped")

    async def add_data(self, data_point: DataPoint):
        """添加数据到处理队列"""
        await self.processing_queue.put(data_point)

    async def _processing_loop(self):
        """处理循环"""
        while self.is_running:
            try:
                # 获取数据
                data_point = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                
                # 验证数据
                validated_data = self.validate_data(data_point)
                if not validated_data:
                    logger.warning(f"Invalid data received from flight {data_point.flight_id}")
                    continue
                
                # 异常检测
                anomalies = await self.detect_anomalies(data_point)
                if anomalies:
                    logger.warning(f"Anomalies detected in flight {data_point.flight_id}: {anomalies}")
                    await self.handle_anomalies(data_point, anomalies)
                
                # 存储数据
                await self.store_data(data_point)
                
                # 触发后续处理
                await self.trigger_downstream_processing(data_point)
                
            except asyncio.TimeoutError:
                continue  # 队列为空，继续循环
            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}")

    def validate_data(self, data_point: DataPoint) -> bool:
        """验证数据的有效性"""
        try:
            data = data_point.data
            
            # 检查必要字段
            required_fields = ['timestamp']
            if data_point.data_type == DataType.TELEMETRY:
                required_fields.extend(['latitude', 'longitude', 'altitude'])
            
            for field in required_fields:
                if field not in data:
                    return False
            
            # 检查数值范围
            for field, limits in self.validation_rules.items():
                if field in data:
                    value = data[field]
                    if not isinstance(value, (int, float)):
                        continue
                    if value < limits['min'] or value > limits['max']:
                        logger.warning(f"Field {field} out of range: {value}")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            return False

    async def detect_anomalies(self, data_point: DataPoint) -> List[str]:
        """检测数据中的异常"""
        anomalies = []
        
        try:
            flight_id = data_point.flight_id
            current_data = data_point.data
            
            # 获取历史数据进行比较
            if flight_id in self.data_buffer and len(self.data_buffer[flight_id]) > 0:
                last_data = self.data_buffer[flight_id][-1].data
                
                # 检查位置突变
                if 'latitude' in current_data and 'longitude' in current_data:
                    lat_diff = abs(current_data['latitude'] - last_data.get('latitude', 0))
                    lon_diff = abs(current_data['longitude'] - last_data.get('longitude', 0))
                    
                    if lat_diff > self.anomaly_thresholds['position_drift'] or \
                       lon_diff > self.anomaly_thresholds['position_drift']:
                        anomalies.append("position_drift")
                
                # 检查速度突变
                if 'speed' in current_data:
                    speed_diff = abs(current_data['speed'] - last_data.get('speed', 0))
                    if speed_diff > self.anomaly_thresholds['speed_change']:
                        anomalies.append("speed_anomaly")
                
                # 检查高度突变
                if 'altitude' in current_data:
                    alt_diff = abs(current_data['altitude'] - last_data.get('altitude', 0))
                    if alt_diff > self.anomaly_thresholds['altitude_change']:
                        anomalies.append("altitude_anomaly")
            
            # 检查数据时间戳（是否过于陈旧）
            time_diff = datetime.utcnow() - data_point.timestamp
            if time_diff > timedelta(seconds=30):  # 数据超过30秒认为过时
                anomalies.append("stale_data")
                
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
        
        return anomalies

    async def handle_anomalies(self, data_point: DataPoint, anomalies: List[str]):
        """处理检测到的异常"""
        # 这里可以实现具体的异常处理逻辑
        # 例如：发送警报、记录日志、触发安全措施等
        logger.info(f"Handling anomalies for flight {data_point.flight_id}: {anomalies}")
        
        # 可能的操作：
        # 1. 发送警报通知
        # 2. 记录到异常数据库
        # 3. 触发备用方案
        # 4. 请求人工干预

    async def store_data(self, data_point: DataPoint):
        """存储数据"""
        try:
            flight_id = data_point.flight_id
            
            # 将数据添加到缓冲区
            if flight_id not in self.data_buffer:
                self.data_buffer[flight_id] = []
            
            self.data_buffer[flight_id].append(data_point)
            
            # 限制缓冲区大小，防止内存溢出
            if len(self.data_buffer[flight_id]) > 10000:
                self.data_buffer[flight_id] = self.data_buffer[flight_id][-5000:]  # 保留最新的5000条记录
            
            # 这里可以添加数据持久化逻辑
            # 例如：写入数据库、发送到消息队列等
            
        except Exception as e:
            logger.error(f"Error storing data: {str(e)}")

    async def trigger_downstream_processing(self, data_point: DataPoint):
        """触发下游处理"""
        # 这里可以触发各种下游处理流程
        # 例如：机器学习推理、统计分析、路径规划等
        
        # 示例：如果包含GPS数据，触发路径分析
        if data_point.data_type in [DataType.TELEMETRY, DataType.GPS]:
            await self.analyze_flight_path(data_point)

    async def analyze_flight_path(self, data_point: DataPoint):
        """分析飞行路径"""
        try:
            flight_id = data_point.flight_id
            if flight_id not in self.data_buffer:
                return
            
            # 获取最近的数据点进行路径分析
            recent_data = self.data_buffer[flight_id][-10:]  # 最近10个数据点
            
            if len(recent_data) < 2:
                return
            
            # 计算一些基本指标
            total_distance = 0
            avg_speed = 0
            direction_changes = 0
            
            for i in range(1, len(recent_data)):
                prev_data = recent_data[i-1].data
                curr_data = recent_data[i].data
                
                # 计算距离变化
                if 'latitude' in prev_data and 'longitude' in prev_data and \
                   'latitude' in curr_data and 'longitude' in curr_data:
                    dist = self.calculate_distance(
                        prev_data['latitude'], prev_data['longitude'],
                        curr_data['latitude'], curr_data['longitude']
                    )
                    total_distance += dist
            
            # 如果有足够的数据，可以进行更复杂的分析
            if total_distance > 0:
                logger.info(f"Flight {flight_id} - Total distance: {total_distance:.2f}m")
                
        except Exception as e:
            logger.error(f"Error analyzing flight path: {str(e)}")

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间的距离（使用简化公式）"""
        import math
        
        # 转换为弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半径（米）
        r = 6371000
        return c * r

# 全局处理器实例
processor = RealTimeProcessor()

async def initialize_processor():
    """初始化处理器"""
    await processor.start()
    return processor

if __name__ == "__main__":
    # 测试代码
    async def test_processor():
        await initialize_processor()
        
        # 创建测试数据点
        test_data = DataPoint(
            flight_id="TEST001",
            data_type=DataType.TELEMETRY,
            timestamp=datetime.utcnow(),
            data={
                "latitude": 39.9042,
                "longitude": 116.4074,
                "altitude": 100,
                "speed": 50,
                "heading": 45
            },
            source="simulator"
        )
        
        # 添加数据到处理器
        await processor.add_data(test_data)
        
        # 等待处理
        await asyncio.sleep(2)
        
        # 停止处理器
        await processor.stop()

    # 运行测试
    asyncio.run(test_processor())