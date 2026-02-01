"""
许愿小程序后端API
使用FastAPI和SQLite
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
from datetime import datetime
import json

# 创建应用
app = FastAPI(
    title="许愿小程序 API",
    description="现代简约风格的许愿小程序后端API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库初始化
DATABASE = "wishes.db"

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # 创建愿望表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            likes INTEGER DEFAULT 0
        )
    ''')
    
    # 创建点赞表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wish_id INTEGER,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wish_id) REFERENCES wishes (id),
            UNIQUE(wish_id, ip_address)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    return conn

# 数据模型
class WishCreate(BaseModel):
    content: str

class WishResponse(BaseModel):
    id: int
    content: str
    created_at: str
    likes: int
    liked_by_user: bool = False

# API路由
@app.on_event("startup")
def startup_event():
    """应用启动时初始化数据库"""
    init_db()

@app.get("/")
def read_root():
    """首页"""
    return {"message": "许愿小程序 API", "version": "1.0.0"}

@app.get("/api/wishes", response_model=List[WishResponse])
def get_wishes(skip: int = 0, limit: int = 100):
    """获取愿望列表，按点赞数降序排列"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 查询愿望，按点赞数降序排列
    cursor.execute('''
        SELECT w.id, w.content, w.created_at, w.likes,
               COUNT(l.id) as current_likes
        FROM wishes w
        LEFT JOIN likes l ON w.id = l.wish_id
        GROUP BY w.id
        ORDER BY current_likes DESC, w.created_at DESC
        LIMIT ? OFFSET ?
    ''', (limit, skip))
    
    rows = cursor.fetchall()
    conn.close()
    
    # 转换为字典列表
    wishes = []
    for row in rows:
        wish = {
            "id": row["id"],
            "content": row["content"],
            "created_at": row["created_at"],
            "likes": row["current_likes"],
            "liked_by_user": False  # 后续根据IP判断
        }
        wishes.append(wish)
    
    return wishes

@app.post("/api/wishes", response_model=WishResponse)
def create_wish(wish: WishCreate):
    """创建新愿望"""
    if not wish.content.strip():
        raise HTTPException(status_code=400, detail="愿望内容不能为空")
    
    if len(wish.content.strip()) > 500:
        raise HTTPException(status_code=400, detail="愿望内容不能超过500字符")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO wishes (content) VALUES (?)",
        (wish.content.strip(),)
    )
    wish_id = cursor.lastrowid
    
    # 获取刚插入的愿望
    cursor.execute(
        "SELECT id, content, created_at, likes FROM wishes WHERE id = ?",
        (wish_id,)
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    
    return {
        "id": row["id"],
        "content": row["content"],
        "created_at": row["created_at"],
        "likes": row["likes"],
        "liked_by_user": False
    }

@app.post("/api/wishes/{wish_id}/like")
def like_wish(wish_id: int, request: Request):
    """点赞愿望"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查愿望是否存在
    cursor.execute("SELECT id FROM wishes WHERE id = ?", (wish_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="愿望不存在")
    
    # 获取客户端IP（这里简化处理，实际生产环境需要考虑代理等复杂情况）
    client_ip = request.client.host
    
    try:
        # 尝试插入点赞记录
        cursor.execute(
            "INSERT INTO likes (wish_id, ip_address) VALUES (?, ?)",
            (wish_id, client_ip)
        )
        
        # 更新愿望的点赞数
        cursor.execute(
            "UPDATE wishes SET likes = likes + 1 WHERE id = ?",
            (wish_id,)
        )
        
        conn.commit()
        conn.close()
        
        return {"message": "点赞成功", "wish_id": wish_id}
    except sqlite3.IntegrityError:
        # 如果违反唯一约束，说明已经点过赞了
        conn.close()
        raise HTTPException(status_code=400, detail="您已经点过赞了")

@app.delete("/api/wishes/{wish_id}/like")
def unlike_wish(wish_id: int, request: Request):
    """取消点赞"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查愿望是否存在
    cursor.execute("SELECT id FROM wishes WHERE id = ?", (wish_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="愿望不存在")
    
    # 获取客户端IP
    client_ip = request.client.host
    
    # 删除点赞记录
    cursor.execute(
        "DELETE FROM likes WHERE wish_id = ? AND ip_address = ?",
        (wish_id, client_ip)
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail="您还没有点赞")
    
    # 更新愿望的点赞数
    cursor.execute(
        "UPDATE wishes SET likes = likes - 1 WHERE id = ?",
        (wish_id,)
    )
    
    conn.commit()
    conn.close()
    
    return {"message": "取消点赞成功", "wish_id": wish_id}

@app.get("/api/wishes/{wish_id}", response_model=WishResponse)
def get_wish(wish_id: int):
    """获取单个愿望详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, content, created_at, likes FROM wishes WHERE id = ?",
        (wish_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="愿望不存在")
    
    return {
        "id": row["id"],
        "content": row["content"],
        "created_at": row["created_at"],
        "likes": row["likes"],
        "liked_by_user": False
    }

@app.delete("/api/wishes/{wish_id}")
def delete_wish(wish_id: int):
    """删除愿望（仅用于管理，实际应用中可能不需要）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM wishes WHERE id = ?", (wish_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="愿望不存在")
    
    cursor.execute("DELETE FROM likes WHERE wish_id = ?", (wish_id,))
    cursor.execute("DELETE FROM wishes WHERE id = ?", (wish_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "删除成功", "wish_id": wish_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)