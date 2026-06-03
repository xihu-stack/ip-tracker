from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base, SessionLocal
from models import Admin
from auth import hash_password
from routers import report, query, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    # 数据库迁移：为旧表添加 last_seen_at 字段
    import sqlalchemy
    with engine.connect() as conn:
        try:
            conn.execute(sqlalchemy.text("ALTER TABLE employees ADD COLUMN last_seen_at DATETIME"))
            conn.commit()
            # 将已有行的 last_seen_at 设为 created_at（避免 NULL 导致查询报错）
            conn.execute(sqlalchemy.text("UPDATE employees SET last_seen_at = created_at WHERE last_seen_at IS NULL"))
            conn.commit()
            print("[startup] 已添加 employees.last_seen_at 字段")
        except Exception:
            pass  # 字段已存在，忽略

    # 首次启动自动创建默认管理员
    db = SessionLocal()
    try:
        if db.query(Admin).count() == 0:
            db.add(Admin(username="admin", hashed_password=hash_password("admin123")))
            db.commit()
            print("[startup] 默认管理员已创建: admin / admin123")
    finally:
        db.close()

    yield


app = FastAPI(title="IP 定位追踪平台", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report.router)
app.include_router(query.router)
app.include_router(auth.router)

# 前端静态文件（生产环境）
import os
_dir = os.path.dirname(os.path.abspath(__file__))
# 按优先级搜索：server目录的上级/frontend/dist → 当前工作目录/frontend/dist
_candidates = [
    os.path.join(_dir, "..", "frontend", "dist"),
    os.path.join(os.getcwd(), "frontend", "dist"),
]
dist_path = None
for p in _candidates:
    if os.path.exists(p):
        dist_path = p
        break
if dist_path:
    # SPA 兜底：非 API 路径返回 index.html，交给 Vue Router 处理
    from starlette.responses import FileResponse

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        file_path = os.path.join(dist_path, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_path, "index.html"))

    # 静态资源（JS/CSS/JSON 等文件）
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="static")
    app.mount("/china.json", StaticFiles(directory=dist_path, html=True), name="china")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
