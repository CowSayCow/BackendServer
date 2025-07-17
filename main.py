from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from database import init_db, save_count, get_all_latest, import_locations_from_csv
from database import camera_id_exists


# 許可するIPアドレスリスト
ALLOWED_IPS = [
    "127.0.0.1",  # ローカル
    # "192.168.1.100",  # 例: 特定のカメラIP
]

app = FastAPI()

# DB初期化
init_db()
import_locations_from_csv()

# CORS設定（必要に応じて変更）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# モデル定義
class PeopleCount(BaseModel):
    camera_id: str
    timestamp: datetime
    count: int


# IP制限用の依存関数
def verify_ip(request: Request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail=f"Access denied from IP: {client_ip}")

# エンドポイント
@app.post("/api/people_count")
async def receive_count(data: PeopleCount, request: Request = Depends(verify_ip)):
    if not camera_id_exists(data.camera_id):
        raise HTTPException(status_code=400, detail="camera_id is not registered in locations table")
    save_count(data.camera_id, data.timestamp.isoformat(), data.count)
    return {"status": "ok"}

# 混雑一覧表示用(メインページ)
@app.get("/api/congestion")
async def congestion():
    return get_all_latest()