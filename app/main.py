# app/main.py
import uvicorn
from fastapi import FastAPI
from app.routers.devops import router as devops_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="DevOps AI Team FastAPI", version="1.0")

app.include_router(devops_router)

@app.get("/")
async def root() -> dict:
    return {"message": "DevOps AI Team FastAPI is running!"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
