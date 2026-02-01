"""
空中自动驾驶大数据平台 - 演示脚本
展示平台的主要功能
"""
import asyncio
import json
from datetime import datetime, timedelta
import numpy as np

# 导入平台组件
from data_processing.realtime_processor import RealTimeProcessor, DataPoint, DataType
from ml_models.flight_prediction import FlightPathPredictor, SafetyAnalyzer
from visualization.map_visualizer import MapVisualizer, DashboardGenerator


async def run_demo():
    print("="*60)
    print("空中自动驾驶大数据平台 - 功能演示")
    print("="*60)
    
    print("\n1. 初始化平台组件...")
    
    # 初始化实时处理器
    processor = RealTimeProcessor()
    await processor.start()
    print("   ✓ 实时处理器已启动")
    
    # 初始化机器学习预测器
    predictor = FlightPathPredictor()
    print("   ✓ 机器学习预测器已准备")
    
    # 初始化安全分析器
    safety_analyzer = SafetyAnalyzer()
    print("   ✓ 安全分析器已准备")
    
    # 初始化可视化器
    visualizer = MapVisualizer()
    print("   ✓ 可视化器已准备")
    
    print("\n2. 生成模拟飞行数据...")
    
    # 生成模拟飞行数据
    def generate_flight_data(flight_id, num_points=20):
        data = []
        start_lat = 39.9042 + np.random.uniform(-0.01, 0.01)
        start_lng = 116.4074 + np.random.uniform(-0.01, 0.01)
        start_alt = 100 + np.random.uniform(-20, 20)
        
        for i in range(num_points):
            timestamp = datetime.utcnow() - timedelta(minutes=num_points-i)
            
            data.append({
                'latitude': start_lat + np.random.uniform(-0.0005, 0.0005) * i,
                'longitude': start_lng + np.random.uniform(-0.0005, 0.0005) * i,
                'altitude': start_alt + np.random.uniform(-5, 5) + i * 2,
                'speed': 40 + np.random.uniform(-10, 10),
                'heading': np.random.uniform(0, 360),
                'battery_level': 100 - i * 0.8,
                'wind_speed': np.random.uniform(0, 15),
                'wind_direction': np.random.uniform(0, 360),
                'temperature': 20 + np.random.uniform(-5, 5),
                'humidity': 50 + np.random.uniform(-20, 20),
                'pressure': 1013 + np.random.uniform(-30, 30),
                'timestamp': timestamp.isoformat()
            })
        
        return data
    
    # 生成多架飞行器的数据
    flight_ids = ['FLIGHT_001', 'FLIGHT_002', 'FLIGHT_003']
    all_flight_data = {}
    
    for flight_id in flight_ids:
        all_flight_data[flight_id] = generate_flight_data(flight_id)
        print(f"   ✓ 生成了 {flight_id} 的 {len(all_flight_data[flight_id])} 个数据点")
    
    print("\n3. 训练机器学习模型...")
    
    # 使用生成的数据训练模型
    training_data = list(all_flight_data.values())
    metrics = predictor.train(training_data)
    
    print(f"   ✓ 模型训练完成 - R² Score: {metrics['r2_score']:.4f}")
    print(f"   ✓ 训练样本数: {metrics['train_samples']}")
    
    print("\n4. 实时数据处理演示...")
    
    # 模拟实时数据流入
    for i, flight_data in enumerate(all_flight_data['FLIGHT_001'][:5]):  # 只处理前5个点
        data_point = DataPoint(
            flight_id='FLIGHT_001',
            data_type=DataType.TELEMETRY,
            timestamp=datetime.utcnow(),
            data=flight_data
        )
        
        await processor.add_data(data_point)
        print(f"   ✓ 处理了第 {i+1} 个实时数据点")
    
    print("\n5. 飞行路径预测演示...")
    
    # 使用最后的状态进行预测
    last_state = all_flight_data['FLIGHT_001'][-1]
    predicted_trajectory = predictor.predict_trajectory(last_state, steps=10)
    
    print(f"   ✓ 预测了未来 10 个位置点")
    print(f"   ✓ 起始位置: ({last_state['latitude']:.6f}, {last_state['longitude']:.6f})")
    print(f"   ✓ 预测终点: ({predicted_trajectory[-1]['predicted_latitude']:.6f}, {predicted_trajectory[-1]['predicted_longitude']:.6f})")
    
    print("\n6. 安全分析演示...")
    
    # 定义一些虚拟障碍物
    obstacles = [
        {'latitude': 39.9060, 'longitude': 116.4090, 'id': 'OBSTACLE_TOWER_1'},
        {'latitude': 39.9030, 'longitude': 116.4060, 'id': 'OBSTACLE_BUILDING_1'}
    ]
    
    # 进行安全分析
    safety_result = safety_analyzer.analyze_safety(predicted_trajectory, obstacles)
    
    print(f"   ✓ 安全分析完成 - 整体风险: {safety_result['overall_risk']}")
    print(f"   ✓ 发现安全问题: {len(safety_result['safety_issues'])} 个")
    print(f"   ✓ 安全点比例: {safety_result['safe_points_ratio']:.2%}")
    
    print("\n7. 可视化演示...")
    
    # 生成可视化
    dashboard_gen = DashboardGenerator()
    
    # 添加一些虚拟的禁飞区
    no_fly_zones = [{
        'id': 'RESTRICTED_AREA_1',
        'coordinates': [
            [39.9070, 116.4100],
            [39.9070, 116.4120],
            [39.9050, 116.4120],
            [39.9050, 116.4100]
        ]
    }]
    
    # 生成仪表板
    dashboard_html = dashboard_gen.generate_dashboard(
        flights_data=all_flight_data,
        predicted_trajectories={'FLIGHT_001': predicted_trajectory},
        obstacles=obstacles,
        no_fly_zones=no_fly_zones
    )
    
    print("   ✓ 生成了综合仪表板")
    
    # 保存仪表板到文件
    with open("demo_dashboard.html", "w", encoding="utf-8") as f:
        f.write(dashboard_html)
    print("   ✓ 仪表板已保存为 demo_dashboard.html")
    
    print("\n8. 数据摘要...")
    
    total_flights = len(all_flight_data)
    total_points = sum(len(data) for data in all_flight_data.values())
    avg_points_per_flight = total_points / total_flights if total_flights > 0 else 0
    
    print(f"   ✓ 总飞行器数量: {total_flights}")
    print(f"   ✓ 总数据点数: {total_points}")
    print(f"   ✓ 平均每架飞行器数据点数: {avg_points_per_flight:.1f}")
    print(f"   ✓ 预测点数: {len(predicted_trajectory)}")
    
    print("\n" + "="*60)
    print("演示完成！")
    print("主要功能已展示:")
    print("- 实时数据处理")
    print("- 机器学习预测")
    print("- 安全分析")
    print("- 可视化仪表板")
    print("="*60)
    
    # 停止处理器
    await processor.stop()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(run_demo())