// 空中自动驾驶辅助降落系统
class LandingAssistSystem {
    constructor() {
        this.isInitialized = false;
        this.selectedTarget = null;
        this.currentPosition = { x: 400, y: 300 }; // 初始位置
        this.altitude = 120; // 当前高度
        this.speed = 5.2; // 当前速度
        this.battery = 85; // 电池电量
        this.flightStatus = '飞行中'; // 飞行状态
        this.landingMode = 'precision'; // 降落模式
        this.isLanding = false; // 是否正在降落
        this.isManualMode = false; // 是否手动模式
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.drawCameraView();
        this.updateStatusDisplay();
        this.startSimulation();
        this.isInitialized = true;
        
        console.log('🎯 空中自动驾驶辅助降落系统已初始化');
    }

    setupEventListeners() {
        // 摄像头视图点击事件
        const overlay = document.getElementById('camera-overlay');
        overlay.style.pointerEvents = 'auto'; // 允许点击事件
        
        overlay.addEventListener('click', (e) => {
            if (this.isManualMode || this.isLanding) return;
            
            const rect = overlay.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            this.selectLandingTarget(x, y);
        });

        // 控制按钮事件
        document.getElementById('takeoff-btn').addEventListener('click', () => this.takeoff());
        document.getElementById('land-btn').addEventListener('click', () => this.startLanding());
        document.getElementById('cancel-btn').addEventListener('click', () => this.cancelLanding());
        document.getElementById('manual-btn').addEventListener('click', () => this.toggleManualMode());

        // 降落模式选择
        document.querySelectorAll('input[name="landing-mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.landingMode = e.target.value;
                this.updateLandingInfo();
            });
        });

        // 选项勾选
        document.getElementById('obstacle-check').addEventListener('change', (e) => {
            console.log('障碍物检测:', e.target.checked);
        });
        document.getElementById('ground-check').addEventListener('change', (e) => {
            console.log('地面类型检测:', e.target.checked);
        });
    }

    selectLandingTarget(x, y) {
        this.selectedTarget = { x, y };
        
        // 显示目标标记
        const targetElement = document.getElementById('landing-target');
        targetElement.style.display = 'block';
        targetElement.style.left = `${x}px`;
        targetElement.style.top = `${y}px`;
        
        // 计算相对坐标和距离
        const distance = Math.sqrt(
            Math.pow(x - this.currentPosition.x, 2) + 
            Math.pow(y - this.currentPosition.y, 2)
        );
        
        // 显示目标信息
        const coordsElement = document.getElementById('target-coords');
        const distanceElement = document.getElementById('target-distance');
        
        coordsElement.textContent = `X: ${Math.round(x)}, Y: ${Math.round(y)}`;
        distanceElement.textContent = `距离: ${Math.round(distance)}px`;
        
        // 更新降落信息
        this.updateLandingInfo();
        
        // 启用降落按钮
        document.getElementById('land-btn').disabled = false;
        
        // 触发动画效果
        targetElement.classList.add('highlight');
        setTimeout(() => {
            targetElement.classList.remove('highlight');
        }, 500);
        
        console.log(`🎯 选择降落目标: (${x}, ${y}), 距离: ${Math.round(distance)}px`);
    }

    takeoff() {
        if (this.isLanding) return;
        
        this.flightStatus = '起飞中';
        this.updateStatusDisplay();
        
        // 模拟起飞过程
        setTimeout(() => {
            this.flightStatus = '飞行中';
            this.altitude = 120;
            this.updateStatusDisplay();
            
            // 重置当前位置到中心
            this.currentPosition = { x: 400, y: 300 };
            this.updateCurrentPositionDisplay();
            
            console.log('✈️ 起飞完成');
        }, 3000);
        
        console.log('✈️ 开始起飞');
    }

    startLanding() {
        if (!this.selectedTarget || this.isLanding) return;
        
        this.isLanding = true;
        this.flightStatus = '自动降落中';
        
        // 禁用相关按钮
        document.getElementById('land-btn').disabled = true;
        document.getElementById('takeoff-btn').disabled = true;
        document.getElementById('cancel-btn').disabled = false;
        
        this.updateStatusDisplay();
        
        // 开始降落模拟
        this.simulateLanding();
        
        console.log('🛬 开始自动降落');
    }

    simulateLanding() {
        // 模拟降落过程
        const landingSteps = 100; // 降落步数
        let step = 0;
        
        const landingInterval = setInterval(() => {
            step++;
            
            if (step >= landingSteps) {
                // 降落完成
                this.completeLanding();
                clearInterval(landingInterval);
                return;
            }
            
            // 更新高度和位置
            this.altitude = 120 - (step * 1.2);
            this.speed = 5.2 - (step * 0.02);
            
            // 模拟向目标移动
            const dx = (this.selectedTarget.x - this.currentPosition.x) / (landingSteps - step);
            const dy = (this.selectedTarget.y - this.currentPosition.y) / (landingSteps - step);
            
            this.currentPosition.x += dx;
            this.currentPosition.y += dy;
            
            // 随机小幅度调整模拟真实飞行
            this.currentPosition.x += (Math.random() - 0.5) * 2;
            this.currentPosition.y += (Math.random() - 0.5) * 2;
            
            this.updateStatusDisplay();
            this.updateCurrentPositionDisplay();
            
            // 每10步更新一次ETA
            if (step % 10 === 0) {
                this.updateLandingInfo();
            }
        }, 100); // 每100ms更新一次
    }

    completeLanding() {
        this.isLanding = false;
        this.flightStatus = '已降落';
        this.altitude = 0;
        this.speed = 0;
        
        // 更新显示
        this.updateStatusDisplay();
        this.updateCurrentPositionDisplay();
        this.updateLandingInfo();
        
        // 禁用降落按钮，启用起飞按钮
        document.getElementById('land-btn').disabled = true;
        document.getElementById('takeoff-btn').disabled = false;
        document.getElementById('cancel-btn').disabled = true;
        
        // 隐藏目标标记
        document.getElementById('landing-target').style.display = 'none';
        
        // 重置选择的目标
        this.selectedTarget = null;
        
        console.log('✅ 降落完成');
        
        // 显示完成消息
        this.showMessage('降落成功！', 'success');
    }

    cancelLanding() {
        if (!this.isLanding) return;
        
        this.isLanding = false;
        this.flightStatus = '飞行中';
        
        // 重新启用按钮
        document.getElementById('land-btn').disabled = this.selectedTarget ? false : true;
        document.getElementById('takeoff-btn').disabled = false;
        document.getElementById('cancel-btn').disabled = true;
        
        this.updateStatusDisplay();
        
        console.log('❌ 降落已取消');
        this.showMessage('降落已取消', 'warning');
    }

    toggleManualMode() {
        this.isManualMode = !this.isManualMode;
        
        const manualBtn = document.getElementById('manual-btn');
        if (this.isManualMode) {
            manualBtn.textContent = '自动模式';
            manualBtn.style.background = 'linear-gradient(135deg, #10b981, #34d399)';
            this.flightStatus = '手动模式';
            console.log('🎮 切换到手动模式');
        } else {
            manualBtn.textContent = '手动模式';
            manualBtn.style.background = 'linear-gradient(135deg, #6366f1, #8b5cf6)';
            this.flightStatus = '飞行中';
            console.log('🤖 切换到自动模式');
        }
        
        this.updateStatusDisplay();
    }

    updateStatusDisplay() {
        document.getElementById('altitude').textContent = `${Math.round(this.altitude)}m`;
        document.getElementById('speed').textContent = `${this.speed.toFixed(1)} m/s`;
        document.getElementById('battery').textContent = `${this.battery}%`;
        
        const statusElement = document.getElementById('flight-status');
        statusElement.textContent = this.flightStatus;
        
        // 根据状态更新样式
        statusElement.className = 'status-value';
        if (this.flightStatus.includes('降落')) {
            statusElement.classList.add('status-warning');
        } else if (this.flightStatus.includes('起飞')) {
            statusElement.classList.add('status-warning');
        } else if (this.flightStatus.includes('已降落')) {
            statusElement.classList.add('status-active');
        } else if (this.flightStatus.includes('手动')) {
            statusElement.classList.add('status-danger');
        }
    }

    updateCurrentPositionDisplay() {
        const posElement = document.getElementById('current-position');
        if (posElement) {
            posElement.style.left = `${this.currentPosition.x}px`;
            posElement.style.top = `${this.currentPosition.y}px`;
        }
    }

    updateLandingInfo() {
        if (this.selectedTarget) {
            document.getElementById('info-coords').textContent = 
                `X: ${Math.round(this.selectedTarget.x)}, Y: ${Math.round(this.selectedTarget.y)}`;
            
            // 计算ETA (预计到达时间)
            const distance = Math.sqrt(
                Math.pow(this.selectedTarget.x - this.currentPosition.x, 2) + 
                Math.pow(this.selectedTarget.y - this.currentPosition.y, 2)
            );
            
            // 简单的ETA计算 (基于当前速度)
            const eta = distance / this.speed;
            document.getElementById('info-eta').textContent = 
                eta > 0 ? `${Math.round(eta)}s` : '--';
        } else {
            document.getElementById('info-coords').textContent = '--';
            document.getElementById('info-eta').textContent = '--';
        }
        
        // 更新安全等级 (基于当前参数)
        const safetyElement = document.getElementById('info-safety');
        let safetyLevel = 'high';
        
        if (this.altitude < 20) {
            safetyLevel = 'high';
        } else if (this.altitude < 50) {
            safetyLevel = 'medium';
        } else {
            safetyLevel = 'low';
        }
        
        safetyElement.textContent = 
            safetyLevel === 'high' ? '高' : 
            safetyLevel === 'medium' ? '中' : '低';
        safetyElement.className = `info-value safety-${safetyLevel}`;
    }

    drawCameraView() {
        const canvas = document.getElementById('cameraCanvas');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 绘制模拟的地面纹理
        this.drawGroundTexture(ctx, canvas.width, canvas.height);
        
        // 绘制一些模拟的地标和障碍物
        this.drawLandmarks(ctx);
        
        // 绘制当前位置指示器
        this.drawCurrentPositionIndicator(ctx);
    }

    drawGroundTexture(ctx, width, height) {
        // 绘制渐变背景模拟地面
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, '#8B4513'); // 棕色 - 远处
        gradient.addColorStop(0.7, '#A0522D'); // 稍浅的棕色
        gradient.addColorStop(1, '#CD853F'); // 深橙色 - 近处
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);
        
        // 添加一些随机纹理点模拟地面细节
        ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        for (let i = 0; i < 200; i++) {
            const x = Math.random() * width;
            const y = Math.random() * height;
            const size = Math.random() * 2;
            
            ctx.beginPath();
            ctx.arc(x, y, size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    drawLandmarks(ctx) {
        // 绘制一些模拟的地标（建筑物、道路等）
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 2;
        
        // 绘制一些矩形模拟建筑物
        for (let i = 0; i < 15; i++) {
            const x = Math.random() * 700 + 50;
            const y = Math.random() * 500 + 50;
            const width = Math.random() * 60 + 20;
            const height = Math.random() * 80 + 30;
            
            ctx.strokeRect(x, y, width, height);
        }
        
        // 绘制一些线条模拟道路
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.lineWidth = 3;
        
        for (let i = 0; i < 8; i++) {
            const x1 = Math.random() * 700 + 50;
            const y1 = Math.random() * 500 + 50;
            const x2 = x1 + (Math.random() - 0.5) * 200;
            const y2 = y1 + (Math.random() - 0.5) * 200;
            
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }
    }

    drawCurrentPositionIndicator(ctx) {
        // 绘制当前位置指示器
        ctx.fillStyle = 'rgba(59, 130, 246, 0.3)';
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2;
        
        const x = this.currentPosition.x;
        const y = this.currentPosition.y;
        
        // 绘制圆圈
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        
        // 绘制十字线
        ctx.beginPath();
        ctx.moveTo(x - 15, y);
        ctx.lineTo(x + 15, y);
        ctx.moveTo(x, y - 15);
        ctx.lineTo(x, y + 15);
        ctx.stroke();
    }

    startSimulation() {
        // 模拟飞行中的轻微移动
        setInterval(() => {
            if (this.isLanding || this.isManualMode) return;
            
            // 模拟轻微的位置漂移
            this.currentPosition.x += (Math.random() - 0.5) * 0.5;
            this.currentPosition.y += (Math.random() - 0.5) * 0.5;
            
            // 限制在画布范围内
            this.currentPosition.x = Math.max(10, Math.min(790, this.currentPosition.x));
            this.currentPosition.y = Math.max(10, Math.min(590, this.currentPosition.y));
            
            this.updateCurrentPositionDisplay();
            
            // 模拟轻微的高度和速度变化
            if (this.flightStatus === '飞行中') {
                this.altitude += (Math.random() - 0.5) * 0.2;
                this.speed += (Math.random() - 0.5) * 0.1;
                
                // 限制范围
                this.altitude = Math.max(115, Math.min(125, this.altitude));
                this.speed = Math.max(4.5, Math.min(6.0, this.speed));
                
                this.updateStatusDisplay();
            }
        }, 100);
        
        // 模拟电池消耗
        setInterval(() => {
            if (this.flightStatus !== '已降落') {
                this.battery = Math.max(0, this.battery - 0.01);
                this.updateStatusDisplay();
            }
        }, 5000);
    }

    showMessage(message, type = 'info') {
        // 创建消息元素
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${type}`;
        messageEl.textContent = message;
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
            background: ${type === 'success' ? '#10b981' : 
                         type === 'warning' ? '#f59e0b' : 
                         '#374151'};
        `;
        
        document.body.appendChild(messageEl);
        
        // 3秒后移除消息
        setTimeout(() => {
            messageEl.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (messageEl.parentNode) {
                    messageEl.parentNode.removeChild(messageEl);
                }
            }, 300);
        }, 3000);
    }
}

// 添加动画样式到头部
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// 页面加载完成后初始化系统
document.addEventListener('DOMContentLoaded', () => {
    window.landingSystem = new LandingAssistSystem();
});

// 导出类以便调试
window.LandingAssistSystem = LandingAssistSystem;