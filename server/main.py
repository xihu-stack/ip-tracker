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
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
