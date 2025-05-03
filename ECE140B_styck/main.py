from fastapi import FastAPI, Request, Form, HTTPException, WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from typing import Optional, Dict, List
import json
from datetime import datetime

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# In-memory storage (replace with database in production)
users: Dict[str, str] = {}  # username: password
device_status = False
user_weight = 0
gait_data: Dict[str, List[Dict]] = {}  # date: [session_data]

class User(BaseModel):
    username: str
    password: str

class ChangePassword(BaseModel):
    username: str
    currentPassword: str
    newPassword: str

class DeviceStatus(BaseModel):
    status: bool

class UserWeight(BaseModel):
    weight: float

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
    return templates.TemplateResponse("account.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/api/login")
async def login(user: User):
    if user.username in users and users[user.username] == user.password:
        return {"message": "Login successful", "redirect": "/dashboard"}
    return {"message": "Invalid credentials"}

@app.post("/api/register")
async def register(user: User):
    if user.username in users:
        return {"message": "Username already exists"}
    users[user.username] = user.password
    return {"message": "Registration successful"}

@app.post("/api/change-password")
async def change_password(data: ChangePassword):
    if data.username not in users:
        return {"message": "User not found"}
    if users[data.username] != data.currentPassword:
        return {"message": "Current password is incorrect"}
    users[data.username] = data.newPassword
    return {"message": "Password changed successfully"}

@app.post("/api/device-status")
async def update_device_status(status: DeviceStatus):
    global device_status
    device_status = status.status
    return {"message": "Device status updated"}

@app.post("/api/user-weight")
async def update_user_weight(weight: UserWeight):
    global user_weight
    user_weight = weight.weight
    return {"message": "User weight updated"}

@app.get("/api/sessions")
async def get_sessions(date: str):
    if date in gait_data:
        return gait_data[date]
    return []

@app.get("/api/session-data/{session_id}")
async def get_session_data(session_id: str):
    # In a real implementation, you would fetch this from a database
    return []

# WebSocket connection for real-time data
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages
            # In a real implementation, you would process the data and store it
            pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
