"""
地图可视化模块
用于展示飞行器位置、轨迹和相关数据
"""
import folium
from folium import plugins
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
import logging
from branca.colormap import LinearColormap

logger = logging.getLogger(__name__)

class MapVisualizer:
    """
    地图可视化器
    使用folium创建交互式地图来展示飞行数据
    """
    
    def __init__(self, center_lat: float = 39.9042, center_lng: float = 116.4074, zoom_start: int = 13):
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.zoom_start = zoom_start
        self.map = None
        
    def create_map(self) -> folium.Map:
        """
        创建基础地图
        """
        self.map = folium.Map(
            location=[self.center_lat, self.center_lng],
            zoom_start=self.zoom_start,
            tiles='OpenStreetMap'
        )
        
        return self.map
    
    def add_flight_track(self, flight_data: List[Dict], flight_id: str = "Flight Track", 
                        color: str = "blue", weight: int = 3, opacity: float = 0.8):
        """
        在地图上添加飞行轨迹
        """
        if not self.map:
            self.create_map()
        
        if not flight_data:
            logger.warning("No flight data to plot")
            return
        
        # 提取经纬度坐标
        coordinates = []
        for point in flight_data:
            lat = point.get('latitude')
            lng = point.get('longitude')
            if lat is not None and lng is not None:
                coordinates.append([lat, lng])
        
        if coordinates:
            # 添加轨迹线
            folium.PolyLine(
                locations=coordinates,
                color=color,
                weight=weight,
                opacity=opacity,
                popup=f"Flight ID: {flight_id}"
            ).add_to(self.map)
            
            # 添加起始点标记
            if coordinates:
                folium.Marker(
                    location=coordinates[0],
                    popup=f"Start - {flight_id}",
                    icon=folium.Icon(color='green', icon='play')
                ).add_to(self.map)
                
                # 添加终点标记
                folium.Marker(
                    location=coordinates[-1],
                    popup=f"End - {flight_id}",
                    icon=folium.Icon(color='red', icon='stop')
                ).add_to(self.map)
    
    def add_multiple_flights(self, flights_data: Dict[str, List[Dict]], 
                           colors: List[str] = None):
        """
        在地图上添加多条飞行轨迹
        """
        if not colors:
            colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkred', 
                     'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
                     'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 
                     'gray', 'black', 'lightgray']
        
        for i, (flight_id, flight_data) in enumerate(flights_data.items()):
            color = colors[i % len(colors)]
            self.add_flight_track(flight_data, flight_id, color=color)
    
    def add_heatmap(self, flight_data: List[Dict], radius: int = 15, blur: int = 10):
        """
        添加热力图层显示飞行密度
        """
        if not self.map:
            self.create_map()
        
        if not flight_data:
            logger.warning("No flight data for heatmap")
            return
        
        # 提取坐标用于热力图
        heat_data = []
        for point in flight_data:
            lat = point.get('latitude')
            lng = point.get('longitude')
            if lat is not None and lng is not None:
                heat_data.append([lat, lng, 1])  # 第三个值是权重
        
        if heat_data:
            plugins.HeatMap(heat_data, radius=radius, blur=blur).add_to(self.map)
    
    def add_altitude_profile(self, flight_data: List[Dict], flight_id: str = "Altitude Profile"):
        """
        添加高度剖面图（在地图旁边显示）
        """
        if not flight_data:
            logger.warning("No flight data for altitude profile")
            return
        
        # 提取时间和高度数据
        times = []
        altitudes = []
        coordinates = []
        
        for point in flight_data:
            lat = point.get('latitude')
            lng = point.get('longitude')
            alt = point.get('altitude')
            timestamp = point.get('timestamp')
            
            if lat is not None and lng is not None and alt is not None:
                coordinates.append([lat, lng])
                altitudes.append(alt)
                
                if timestamp:
                    try:
                        if isinstance(timestamp, str):
                            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            ts = timestamp
                        times.append(ts.strftime('%H:%M:%S'))
                    except:
                        times.append("Unknown")
                else:
                    times.append("Unknown")
        
        if coordinates and altitudes:
            # 创建高度颜色映射
            min_alt = min(altitudes)
            max_alt = max(altitudes)
            
            colormap = LinearColormap(
                colors=['blue', 'yellow', 'red'],
                vmin=min_alt,
                vmax=max_alt,
                caption='Altitude (m)'
            )
            
            # 为每个点着色
            for i, coord in enumerate(coordinates):
                if i < len(altitudes):
                    color = colormap(altitudes[i])
                    folium.CircleMarker(
                        location=coord,
                        radius=5,
                        popup=f"Altitude: {altitudes[i]:.1f}m<br>Time: {times[i] if i < len(times) else 'Unknown'}",
                        color='gray',
                        weight=1,
                        fillColor=color,
                        fillOpacity=0.7
                    ).add_to(self.map)
            
            # 添加颜色图例
            colormap.add_to(self.map)
    
    def add_predicted_trajectory(self, current_position: Dict, predicted_trajectory: List[Dict], 
                               color: str = "orange", dashed: bool = True):
        """
        在地图上添加预测轨迹
        """
        if not self.map:
            self.create_map()
        
        # 创建坐标列表
        coordinates = []
        
        # 添加当前位置
        current_lat = current_position.get('latitude')
        current_lng = current_position.get('longitude')
        if current_lat is not None and current_lng is not None:
            coordinates.append([current_lat, current_lng])
        
        # 添加预测点
        for point in predicted_trajectory:
            lat = point.get('predicted_latitude')
            lng = point.get('predicted_longitude')
            if lat is not None and lng is not None:
                coordinates.append([lat, lng])
        
        if len(coordinates) > 1:
            # 添加预测轨迹线
            if dashed:
                # 使用虚线表示预测轨迹
                folium.PolyLine(
                    locations=coordinates,
                    color=color,
                    weight=3,
                    opacity=0.7,
                    popup="Predicted Trajectory",
                    dash_array="10, 10"  # 创建虚线效果
                ).add_to(self.map)
            
            # 添加预测点标记
            for i, coord in enumerate(coordinates[1:], 1):  # 跳过起始点
                folium.CircleMarker(
                    location=coord,
                    radius=4,
                    popup=f"Predicted Point {i}<br>Altitude: {predicted_trajectory[i-1].get('predicted_altitude', 'N/A'): .1f}m",
                    color=color,
                    fillColor=color,
                    fillOpacity=0.6
                ).add_to(self.map)
    
    def add_obstacles(self, obstacles: List[Dict], radius: int = 50):
        """
        在地图上添加障碍物
        """
        if not self.map:
            self.create_map()
        
        for obstacle in obstacles:
            lat = obstacle.get('latitude')
            lng = obstacle.get('longitude')
            obs_id = obstacle.get('id', 'Unknown')
            
            if lat is not None and lng is not None:
                folium.Circle(
                    location=[lat, lng],
                    radius=radius,
                    popup=f"Obstacle: {obs_id}",
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.3
                ).add_to(self.map)
    
    def add_no_fly_zones(self, zones: List[Dict]):
        """
        在地图上添加禁飞区
        """
        if not self.map:
            self.create_map()
        
        for zone in zones:
            coords = zone.get('coordinates', [])
            zone_id = zone.get('id', 'Unknown')
            
            if coords:
                folium.Polygon(
                    locations=coords,
                    popup=f"No-Fly Zone: {zone_id}",
                    color='red',
                    weight=2,
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.2
                ).add_to(self.map)
    
    def save_map(self, filepath: str):
        """
        保存地图到HTML文件
        """
        if not self.map:
            self.create_map()
        
        self.map.save(filepath)
        logger.info(f"Map saved to {filepath}")
    
    def get_map_html(self) -> str:
        """
        获取地图HTML字符串
        """
        if not self.map:
            self.create_map()
        
        return self.map._repr_html_()

class DashboardGenerator:
    """
    仪表板生成器
    生成包含多个可视化组件的综合仪表板
    """
    
    def __init__(self):
        self.visualizer = MapVisualizer()
    
    def generate_dashboard(self, flights_data: Dict[str, List[Dict]], 
                          predicted_trajectories: Dict[str, List[Dict]] = None,
                          obstacles: List[Dict] = None,
                          no_fly_zones: List[Dict] = None) -> str:
        """
        生成综合仪表板HTML
        """
        # 创建地图
        m = self.visualizer.create_map()
        
        # 添加实际飞行轨迹
        self.visualizer.add_multiple_flights(flights_data)
        
        # 添加预测轨迹（如果有）
        if predicted_trajectories:
            for flight_id, trajectory in predicted_trajectories.items():
                if flight_id in flights_data and len(flights_data[flight_id]) > 0:
                    current_pos = flights_data[flight_id][-1]  # 使用最后一个已知位置
                    self.visualizer.add_predicted_trajectory(current_pos, trajectory)
        
        # 添加障碍物（如果有）
        if obstacles:
            self.visualizer.add_obstacles(obstacles)
        
        # 添加禁飞区（如果有）
        if no_fly_zones:
            self.visualizer.add_no_fly_zones(no_fly_zones)
        
        # 返回HTML内容
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>空中自动驾驶大数据平台 - 飞行监控仪表板</title>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .dashboard-container {{
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                }}
                .map-container {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    background: white;
                }}
                .stats-panel {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-top: 20px;
                }}
                .stat-card {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #667eea;
                }}
                .stat-label {{
                    font-size: 14px;
                    color: #666;
                    margin-top: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>空中自动驾驶大数据平台</h1>
                <p>飞行监控与分析仪表板</p>
            </div>
            
            <div class="dashboard-container">
                <div class="map-container">
                    {self.visualizer.get_map_html()}
                </div>
                
                <div class="stats-panel">
                    <div class="stat-card">
                        <div class="stat-value">{len(flights_data)}</div>
                        <div class="stat-label">活跃飞行器</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{sum(len(data) for data in flights_data.values())}</div>
                        <div class="stat-label">总数据点</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(obstacles) if obstacles else 0}</div>
                        <div class="stat-label">障碍物</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(no_fly_zones) if no_fly_zones else 0}</div>
                        <div class="stat-label">禁飞区</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template

# 使用示例
if __name__ == "__main__":
    # 创建模拟数据
    def generate_sample_flight_data(num_flights=3, points_per_flight=20):
        flights = {}
        
        for i in range(num_flights):
            flight_id = f"FLIGHT_{i+1:03d}"
            flight_data = []
            
            # 随机起始位置
            start_lat = 39.9042 + np.random.uniform(-0.05, 0.05)
            start_lng = 116.4074 + np.random.uniform(-0.05, 0.05)
            
            for j in range(points_per_flight):
                flight_data.append({
                    'latitude': start_lat + np.random.uniform(-0.001, 0.001) * j,
                    'longitude': start_lng + np.random.uniform(-0.001, 0.001) * j,
                    'altitude': 100 + np.random.uniform(-20, 20) + j * 2,
                    'speed': 40 + np.random.uniform(-5, 5),
                    'heading': np.random.uniform(0, 360),
                    'battery_level': 100 - j * 0.5,
                    'timestamp': (datetime.now().timestamp() + j * 10)
                })
            
            flights[flight_id] = flight_data
        
        return flights
    
    def generate_sample_predictions(num_points=5):
        predictions = []
        start_lat, start_lng, start_alt = 39.9050, 116.4080, 120
        
        for i in range(num_points):
            predictions.append({
                'predicted_latitude': start_lat + np.random.uniform(-0.0005, 0.0005) * i,
                'predicted_longitude': start_lng + np.random.uniform(-0.0005, 0.0005) * i,
                'predicted_altitude': start_alt + i * 5
            })
        
        return predictions
    
    print("生成模拟飞行数据...")
    sample_flights = generate_sample_flight_data(3, 15)
    
    print("初始化可视化器...")
    visualizer = MapVisualizer(center_lat=39.9042, center_lng=116.4074)
    
    print("添加飞行轨迹到地图...")
    visualizer.add_multiple_flights(sample_flights)
    
    print("添加高度剖面...")
    for flight_id, flight_data in sample_flights.items():
        visualizer.add_altitude_profile(flight_data, flight_id)
    
    print("添加预测轨迹...")
    predictions = generate_sample_predictions(5)
    if sample_flights:
        first_flight_data = list(sample_flights.values())[0]
        visualizer.add_predicted_trajectory(first_flight_data[-1], predictions)
    
    print("添加障碍物...")
    obstacles = [
        {'latitude': 39.9060, 'longitude': 116.4090, 'id': 'Building_A'},
        {'latitude': 39.9030, 'longitude': 116.4060, 'id': 'Tower_B'}
    ]
    visualizer.add_obstacles(obstacles)
    
    print("保存地图...")
    visualizer.save_map("sample_flight_map.html")
    
    print("生成综合仪表板...")
    dashboard_gen = DashboardGenerator()
    dashboard_html = dashboard_gen.generate_dashboard(
        flights_data=sample_flights,
        predicted_trajectories={'FLIGHT_001': predictions},
        obstacles=obstacles
    )
    
    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(dashboard_html)
    
    print("可视化完成！地图已保存为 'sample_flight_map.html'")
    print("仪表板已保存为 'dashboard.html'")