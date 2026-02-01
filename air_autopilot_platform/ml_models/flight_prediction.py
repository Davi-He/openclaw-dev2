"""
飞行路径预测模型
使用机器学习算法预测飞行器的未来路径
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pickle
import os

logger = logging.getLogger(__name__)

class FlightPathPredictor:
    """
    飞行路径预测器
    使用历史飞行数据预测未来的飞行路径
    """
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = [
            'current_latitude', 'current_longitude', 'current_altitude',
            'current_speed', 'current_heading', 'current_battery',
            'wind_speed', 'wind_direction', 'temperature', 
            'humidity', 'pressure', 'time_of_day'
        ]
        
    def prepare_features(self, flight_data: List[Dict]) -> np.ndarray:
        """
        准备特征数据
        """
        features = []
        
        for i in range(len(flight_data)-1):
            current = flight_data[i]
            next_point = flight_data[i+1]
            
            # 当前状态特征
            feature_row = [
                current.get('latitude', 0),
                current.get('longitude', 0), 
                current.get('altitude', 0),
                current.get('speed', 0),
                current.get('heading', 0),
                current.get('battery_level', 100),
                current.get('wind_speed', 0),  # 假设有风速数据
                current.get('wind_direction', 0),  # 假设有风向数据
                current.get('temperature', 25),  # 假设有温度数据
                current.get('humidity', 50),  # 假设有湿度数据
                current.get('pressure', 1013),  # 假设有气压数据
                self._get_time_of_day(current.get('timestamp'))  # 时间段特征
            ]
            
            features.append(feature_row)
        
        return np.array(features)
    
    def prepare_targets(self, flight_data: List[Dict]) -> np.ndarray:
        """
        准备目标数据（下一个位置点）
        """
        targets = []
        
        for i in range(len(flight_data)-1):
            next_point = flight_data[i+1]
            
            # 目标：下一个位置点
            target_row = [
                next_point.get('latitude', 0),
                next_point.get('longitude', 0),
                next_point.get('altitude', 0)
            ]
            
            targets.append(target_row)
        
        return np.array(targets)
    
    def _get_time_of_day(self, timestamp) -> float:
        """
        将时间转换为时间段特征 (0-24)
        """
        if timestamp is None:
            return 12.0  # 默认中午12点
        
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        return timestamp.hour + timestamp.minute / 60.0
    
    def train(self, flight_data: List[List[Dict]]) -> Dict[str, float]:
        """
        训练模型
        """
        logger.info("开始训练飞行路径预测模型...")
        
        all_features = []
        all_targets = []
        
        # 从多个飞行记录中提取特征和目标
        for flight_record in flight_data:
            if len(flight_record) < 2:
                continue
                
            features = self.prepare_features(flight_record)
            targets = self.prepare_targets(flight_record)
            
            if len(features) > 0 and len(targets) > 0:
                all_features.append(features)
                all_targets.append(targets)
        
        if not all_features:
            raise ValueError("没有足够的训练数据")
        
        # 合并所有飞行记录的数据
        X = np.vstack(all_features)
        y = np.vstack(all_targets)
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 标准化特征
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 训练模型
        self.model.fit(X_train_scaled, y_train)
        
        # 评估模型
        y_pred = self.model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        self.is_trained = True
        
        logger.info(f"模型训练完成 - MSE: {mse:.6f}, R²: {r2:.6f}")
        
        return {
            'mse': mse,
            'r2_score': r2,
            'train_samples': len(X_train),
            'test_samples': len(X_test)
        }
    
    def predict_next_position(self, current_state: Dict) -> Dict[str, float]:
        """
        预测下一个位置
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        # 准备输入特征
        feature_row = [
            current_state.get('latitude', 0),
            current_state.get('longitude', 0),
            current_state.get('altitude', 0),
            current_state.get('speed', 0),
            current_state.get('heading', 0),
            current_state.get('battery_level', 100),
            current_state.get('wind_speed', 0),
            current_state.get('wind_direction', 0),
            current_state.get('temperature', 25),
            current_state.get('humidity', 50),
            current_state.get('pressure', 1013),
            self._get_time_of_day(current_state.get('timestamp'))
        ]
        
        X = np.array([feature_row])
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        
        return {
            'predicted_latitude': float(prediction[0]),
            'predicted_longitude': float(prediction[1]),
            'predicted_altitude': float(prediction[2])
        }
    
    def predict_trajectory(self, current_state: Dict, steps: int = 10) -> List[Dict[str, float]]:
        """
        预测未来轨迹（多步预测）
        """
        trajectory = []
        current = current_state.copy()
        
        for _ in range(steps):
            next_pos = self.predict_next_position(current)
            trajectory.append(next_pos)
            
            # 更新当前状态用于下一步预测
            current.update({
                'latitude': next_pos['predicted_latitude'],
                'longitude': next_pos['predicted_longitude'],
                'altitude': next_pos['predicted_altitude'],
                'timestamp': datetime.utcnow() + timedelta(seconds=(_+1)*5)  # 假设每5秒一个点
            })
        
        return trajectory
    
    def save_model(self, filepath: str):
        """
        保存模型
        """
        if not self.is_trained:
            raise ValueError("无法保存未训练的模型")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained,
            'feature_columns': self.feature_columns
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"模型已保存到 {filepath}")
    
    def load_model(self, filepath: str):
        """
        加载模型
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"模型文件不存在: {filepath}")
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.is_trained = model_data['is_trained']
        self.feature_columns = model_data['feature_columns']
        
        logger.info(f"模型已从 {filepath} 加载")

class SafetyAnalyzer:
    """
    安全分析器
    分析飞行路径的安全性
    """
    
    def __init__(self):
        self.safety_thresholds = {
            'min_altitude': 10,      # 最小安全高度（米）
            'max_altitude': 1000,    # 最大安全高度（米）
            'max_speed': 100,        # 最大安全速度（km/h）
            'proximity_radius': 100, # 接近警告半径（米）
            'battery_min': 15        # 最低电量百分比
        }
    
    def analyze_safety(self, predicted_trajectory: List[Dict], 
                      obstacles: List[Dict] = None,
                      no_fly_zones: List[Dict] = None) -> Dict[str, any]:
        """
        分析轨迹安全性
        """
        safety_issues = []
        overall_risk = "LOW"
        
        for i, point in enumerate(predicted_trajectory):
            # 检查高度限制
            if point['predicted_altitude'] < self.safety_thresholds['min_altitude']:
                safety_issues.append({
                    'type': 'altitude_low',
                    'point_index': i,
                    'value': point['predicted_altitude'],
                    'threshold': self.safety_thresholds['min_altitude'],
                    'severity': 'HIGH'
                })
                overall_risk = max(overall_risk, "HIGH")
            
            elif point['predicted_altitude'] > self.safety_thresholds['max_altitude']:
                safety_issues.append({
                    'type': 'altitude_high', 
                    'point_index': i,
                    'value': point['predicted_altitude'],
                    'threshold': self.safety_thresholds['max_altitude'],
                    'severity': 'HIGH'
                })
                overall_risk = max(overall_risk, "HIGH")
        
        # 检查障碍物接近情况（如果提供了障碍物数据）
        if obstacles:
            for i, pred_point in enumerate(predicted_trajectory):
                for obstacle in obstacles:
                    distance = self._calculate_distance(
                        pred_point['predicted_latitude'],
                        pred_point['predicted_longitude'],
                        obstacle['latitude'],
                        obstacle['longitude']
                    )
                    
                    if distance < self.safety_thresholds['proximity_radius']:
                        safety_issues.append({
                            'type': 'obstacle_proximity',
                            'point_index': i,
                            'distance': distance,
                            'obstacle_id': obstacle.get('id'),
                            'severity': 'MEDIUM' if distance > 50 else 'HIGH'
                        })
                        
                        if distance < 50:
                            overall_risk = max(overall_risk, "HIGH")
        
        return {
            'overall_risk': overall_risk,
            'safety_issues': safety_issues,
            'safe_points_ratio': max(0, (len(predicted_trajectory) - len(safety_issues)) / len(predicted_trajectory)),
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两点间距离（米）
        """
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

# 使用示例
if __name__ == "__main__":
    # 创建模拟训练数据
    def generate_sample_flight_data(num_records=50):
        flight_data = []
        
        for flight_id in range(num_records):
            record = []
            base_lat = 39.9042 + np.random.uniform(-0.1, 0.1)
            base_lon = 116.4074 + np.random.uniform(-0.1, 0.1)
            base_alt = 100 + np.random.uniform(-50, 100)
            
            for t in range(20):  # 每次飞行20个点
                timestamp = datetime.utcnow() - timedelta(minutes=(20-t))
                
                record.append({
                    'latitude': base_lat + np.random.uniform(-0.001, 0.001) * t,
                    'longitude': base_lon + np.random.uniform(-0.001, 0.001) * t,
                    'altitude': base_alt + np.random.uniform(-5, 5) * t,
                    'speed': 50 + np.random.uniform(-10, 10),
                    'heading': np.random.uniform(0, 360),
                    'battery_level': 100 - t * 0.5,
                    'wind_speed': np.random.uniform(0, 10),
                    'wind_direction': np.random.uniform(0, 360),
                    'temperature': 25 + np.random.uniform(-5, 5),
                    'humidity': 50 + np.random.uniform(-20, 20),
                    'pressure': 1013 + np.random.uniform(-20, 20),
                    'timestamp': timestamp.isoformat()
                })
            
            flight_data.append(record)
        
        return flight_data
    
    print("生成模拟飞行数据...")
    sample_data = generate_sample_flight_data(30)
    
    print("初始化预测模型...")
    predictor = FlightPathPredictor()
    
    print("训练模型...")
    metrics = predictor.train(sample_data)
    print(f"训练完成 - R²: {metrics['r2_score']:.4f}")
    
    # 测试预测
    test_state = {
        'latitude': 39.9042,
        'longitude': 116.4074,
        'altitude': 100,
        'speed': 50,
        'heading': 45,
        'battery_level': 80,
        'wind_speed': 5,
        'wind_direction': 90,
        'temperature': 25,
        'humidity': 50,
        'pressure': 1013,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print("\n预测下一个位置...")
    next_pos = predictor.predict_next_position(test_state)
    print(f"预测位置: ({next_pos['predicted_latitude']:.6f}, {next_pos['predicted_longitude']:.6f}, {next_pos['predicted_altitude']:.2f})")
    
    print("\n预测未来轨迹...")
    trajectory = predictor.predict_trajectory(test_state, steps=5)
    for i, point in enumerate(trajectory):
        print(f"步骤 {i+1}: ({point['predicted_latitude']:.6f}, {point['predicted_longitude']:.6f}, {point['predicted_altitude']:.2f})")
    
    # 安全分析
    print("\n进行安全分析...")
    safety_analyzer = SafetyAnalyzer()
    obstacles = [{'latitude': 39.9050, 'longitude': 116.4080, 'id': 'building_1'}]
    safety_result = safety_analyzer.analyze_safety(trajectory, obstacles=obstacles)
    print(f"总体风险: {safety_result['overall_risk']}")
    print(f"安全隐患数量: {len(safety_result['safety_issues'])}")
    
    print("\n保存模型...")
    predictor.save_model("flight_prediction_model.pkl")
    print("模型已保存!")