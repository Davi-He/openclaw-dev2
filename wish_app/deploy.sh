#!/bin/bash

# 许愿小程序部署脚本

set -e  # 遇到错误时退出

echo "🚀 正在部署许愿小程序..."

# 检查是否安装了必要的工具
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python3"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "❌ Pip 未安装，请先安装 Pip"
    exit 1
fi

echo "✅ 环境检查通过"

# 安装依赖
echo "📦 安装依赖..."
pip install --user --break-system-packages -r requirements.txt

# 启动后端服务
echo "🔌 启动后端服务 (端口 8000)..."
python3 backend.py > backend.log 2>&1 &

# 等待后端服务启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 启动前端服务器
echo "🌐 启动前端服务器 (端口 8080)..."
python3 -m http.server 8080 > frontend.log 2>&1 &

echo "✅ 部署完成!"

echo ""
echo "🎉 许愿小程序已启动!"
echo ""
echo "🔗 访问地址:"
echo "   - 前端页面: http://localhost:8080"
echo "   - API文档: http://localhost:8000/docs"
echo "   - API根路径: http://localhost:8000"
echo ""
echo "🔧 常用命令:"
echo "   - 查看后端日志: tail -f backend.log"
echo "   - 查看前端日志: tail -f frontend.log"
echo "   - 停止服务: pkill -f 'python3.*backend\|python3.*http.server'"
echo ""

echo "✨ 应用已准备好，快去许下你的心愿吧！"