# 许愿小程序

一个现代简约风格的许愿小程序，支持点赞功能，点赞越多排序越靠前。

## 功能特性

- 许愿发布
- 点赞功能
- 按点赞数排序
- 现代简约设计
- 响应式布局

## 技术栈

- **前端**: HTML5, CSS3, JavaScript (原生)
- **后端**: Python, FastAPI
- **数据库**: SQLite (轻量级)
- **样式**: 现代简约设计

## 快速开始

1. 启动后端服务
2. 访问前端页面
3. 开始许愿和点赞

## API接口

- `GET /api/wishes` - 获取愿望列表
- `POST /api/wishes` - 创建新愿望
- `POST /api/wishes/{wish_id}/like` - 点赞
- `DELETE /api/wishes/{wish_id}/like` - 取消点赞