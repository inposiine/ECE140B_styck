from fastapi import FastAPI, Request, Form, HTTPException, WebSocket, WebSocketDisconnect, Query, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from typing import Optional, Dict, List
import json
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
from passlib.context import CryptContext
from pytz import timezone, utc
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
import os
import google.generativeai as genai
import time


app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Database configuration
db_config = {
    'host': 'localhost', 
    'user': 'ECE140B_styck',
    'password': 'ECE140B_class',
    'database': 'stick_db',
    'port': 3307  # Added port configuration
}

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
print(pwd_context.hash("admin123"))

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


device_status = False
user_weight = 0
gait_data: Dict[str, List[Dict]] = {}  # date: [session_data]

# List to keep track of active WebSocket connections
active_connections: list[WebSocket] = []

# Track current session id in memory
current_session_id = None

# Store the threshold in memory (or DB if you want persistence)
current_force_threshold = 0.15  # Default 15%

# Get Gemini API key from environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    
    GEMINI_API_KEY = "AIzaSyBwF9_G2ZW4tc2vWRynF0rA_w1vV6TwRrs"
    print("Warning: GEMINI_API_KEY environment variable not set, using hardcoded key")
else:
    print("Gemini API key loaded from environment variable.")

# Calibration constants
MIN_SPEED = 0.2
MAX_SPEED = 2.0
MIN_FORCE = 5.0
MAX_FORCE = 60.0
MIN_DURATION = 0.2
MAX_DURATION = 2.0

# Normalization functions

def normalize_speed(speed):
    return min(max((speed - MIN_SPEED) / (MAX_SPEED - MIN_SPEED), 0), 1)

def normalize_force(force):
    return min(max((force - MIN_FORCE) / (MAX_FORCE - MIN_FORCE), 0), 1)

def normalize_duration(duration):
    return min(max((duration - MIN_DURATION) / (MAX_DURATION - MIN_DURATION), 0), 1)

# Prompt generation

def generate_prompt(latest, prev1, prev2):
    prompt = f"""
You are an AI walking assistant. Analyze the following gait data and provide a short, actionable suggestion for the user. Focus on safety, comfort, and improvement. Use simple language.

Latest step:
- Gait speed: {latest['gait_speed']:.2f} m/s
- Peak force: {latest['peak_force']:.2f} kg
- Step duration: {latest['duration']:.2f} s

Previous steps:
- Step 2: speed={prev1['gait_speed']:.2f}, force={prev1['peak_force']:.2f}, duration={prev1['duration']:.2f}
- Step 3: speed={prev2['gait_speed']:.2f}, force={prev2['peak_force']:.2f}, duration={prev2['duration']:.2f}

Recent trend:
- Speed: {latest['gait_speed']:.2f} → {prev1['gait_speed']:.2f} → {prev2['gait_speed']:.2f}
- Force: {latest['peak_force']:.2f} → {prev1['peak_force']:.2f} → {prev2['peak_force']:.2f}
- Duration: {latest['duration']:.2f} → {prev1['duration']:.2f} → {prev2['duration']:.2f}

Give a suggestion in 1-2 sentences.
"""
    return prompt

# Suggestion function

def get_suggestion(latest, prev1, prev2, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-2.5-flash-preview-05-20')
    prompt = generate_prompt(latest, prev1, prev2)
    response = model.generate_content(prompt)
    return response.text.strip()

class User(BaseModel):
    username: str
    password: str

class ChangePassword(BaseModel):
    username: str
    currentPassword: str
    newPassword: str

class DeviceStatus(BaseModel):
    status: bool
    user_id: int

class UserWeight(BaseModel):
    weight: float

class UserRegistration(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

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
async def login(user: UserLogin):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True) # Fetch results as dicts
    try:
        cursor.execute("SELECT id, username, password, weight FROM users WHERE username = %s", (user.username,))
        db_user = cursor.fetchone()
        
        if not db_user:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        if not pwd_context.verify(user.password, db_user["password"]):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        # Here you would typically create a session or JWT token
        # For now, just return success and user info (excluding password)
        return {
            "message": "Login successful", 
            "user": {"id": db_user["id"], "username": db_user["username"], "weight": db_user["weight"]},
            "redirect": "/dashboard" # Ensure your frontend uses this
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

@app.post("/api/register")
async def register(user: UserRegistration):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    try:
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        hashed_password = pwd_context.hash(user.password)
        # Insert user without weight, weight will be NULL by default
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (user.username, hashed_password)
        )
        conn.commit()
        return {"message": "Registration successful"}
    except Error as e:
        conn.rollback() # Rollback in case of error
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

@app.post("/api/change-password")
async def change_password(data: ChangePassword):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch user by username
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (data.username,))
        db_user = cursor.fetchone()

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify current password
        if not pwd_context.verify(data.currentPassword, db_user["password"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Hash the new password
        hashed_new_password = pwd_context.hash(data.newPassword)

        # Update the password in the database
        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (hashed_new_password, db_user["id"])
        )
        conn.commit()
        return {"message": "Password changed successfully"}
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

@app.post("/api/device-status")
async def update_device_status(device_status_data: DeviceStatus):
    global device_status, current_session_id
    current_session_id = None
    print("Got status:", device_status_data.status, "for user_id:", device_status_data.user_id)
    device_status = device_status_data.status
    user_id = device_status_data.user_id
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    try:
        if device_status:  # Device turned ON, start new session
            # Check if there's already an active session
            cursor.execute(
                "SELECT id FROM sessions WHERE user_id = %s AND end_time IS NULL ORDER BY start_time DESC LIMIT 1",
                (user_id,)
            )
            active_session = cursor.fetchone()
            if active_session:
                current_session_id = active_session[0]
            else:
                cursor.execute(
                    "INSERT INTO sessions (user_id, start_time) VALUES (%s, NOW())",
                    (user_id,)
                )
                conn.commit()
                current_session_id = cursor.lastrowid
        else:  # Device turned OFF, end current session
            if current_session_id:
                cursor.execute(
                    "UPDATE sessions SET end_time = NOW() WHERE id = %s",
                    (current_session_id,)
                )
                conn.commit()
                current_session_id = None
            else:
                cursor.execute(
                    "UPDATE sessions SET end_time = NOW() WHERE user_id = %s AND end_time IS NULL",
                    (user_id,)
                )
                conn.commit()
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()
    message = {"type": "set_system_status", "active": device_status}
    print(f"Sending device status to ESP32: {message}")
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            print(f"Error sending to websocket {connection.client}: {e}")
    return {"message": "Device status update sent"}

@app.post("/api/user-weight")
async def update_user_weight(weight_data: UserWeight):
    # This endpoint needs proper user authentication and identification (e.g., from a session/JWT)
    # For now, it updates a global variable, which is not ideal for multiple users.
    # To update the database, you would need the user_id.
    # Example if user_id was available:
    # conn = get_db_connection()
    # if conn and user_id:
    #     cursor = conn.cursor()
    #     try:
    #         cursor.execute("UPDATE users SET weight = %s WHERE id = %s", (weight_data.weight, user_id))
    #         conn.commit()
    #         global user_weight # if still using global for immediate effect on current session
    #         user_weight = weight_data.weight
    #         return {"message": "User weight updated in database"}
    #     except Error as e:
    #         conn.rollback()
    #         raise HTTPException(status_code=500, detail=f"Database error: {e}")
    #     finally:
    #         cursor.close()
    #         conn.close()
    # else:
    #     raise HTTPException(status_code=401, detail="User not authenticated or database connection failed")

    global user_weight
    user_weight = weight_data.weight
    return {"message": "User weight updated (globally, not in DB yet for specific user)"}

@app.get("/api/sessions")
async def get_sessions(date: str, user_id: int = Query(...)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch all sessions for the user in the last 2 days (to cover timezone differences)
        cursor.execute(
            "SELECT id, start_time, end_time FROM sessions WHERE user_id = %s AND start_time >= DATE_SUB(%s, INTERVAL 1 DAY) ORDER BY start_time ASC",
            (user_id, date)
        )
        sessions = cursor.fetchall()
        la = timezone('America/Los_Angeles')
        filtered_sessions = []
        for idx, session in enumerate(sessions):
            start_dt = session['start_time']
            end_dt = session['end_time']
            # Convert to local timezone
            if start_dt.tzinfo is None:
                start_dt = utc.localize(start_dt)
            local_start = start_dt.astimezone(la)
            # Only include sessions where the local date matches the selected date (in LA time)
            if local_start.strftime('%Y-%m-%d') == date:
                session['label'] = f"Session {idx+1}"
                session['startTime'] = local_start.strftime('%Y-%m-%d %I:%M:%S %p')
                if end_dt:
                    if end_dt.tzinfo is None:
                        end_dt = utc.localize(end_dt)
                    session['endTime'] = end_dt.astimezone(la).strftime('%Y-%m-%d %I:%M:%S %p')
                else:
                    session['endTime'] = '(active)'
                filtered_sessions.append(session)
        return filtered_sessions
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

@app.get("/api/session-data/{session_id}")
async def get_session_data(session_id: str, user_id: int = Query(...)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT force_value, timestamp FROM force_measurements WHERE session_id = %s ORDER BY timestamp",
            (session_id,)
        )
        data = cursor.fetchall()
        print(f"[DEBUG] Returning {len(data)} force data points for session {session_id}")
        la = timezone('America/Los_Angeles')
        for d in data:
            d['timestamp'] = d['timestamp'].astimezone(la).strftime('%Y-%m-%d %I:%M:%S %p')
        return data
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

@app.get("/api/steps/{session_id}")
async def get_steps(session_id: int, user_id: int = Query(...)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT timestamp, peak_force, gait_speed, accel_profile FROM steps WHERE user_id = %s AND session_id = %s ORDER BY timestamp",
            (user_id, session_id)
        )
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

# WebSocket connection for real-time data
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global current_session_id
    await websocket.accept()
    active_connections.append(websocket)
    print(f"New WebSocket connection established: {websocket.client}")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received WebSocket data: {data}")  # Debug log
            json_data = json.loads(data)
            user_id = json_data.get('user_id', 1)  # Default to 1 if not provided
            if json_data.get('type') in ['force', 'gait']:
                value = json_data.get('value') or json_data.get('force')
                if value is not None:
                    value_kg = float(value) / 1000.0
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            if not current_session_id:
                                cursor.execute(
                                    "SELECT id FROM sessions WHERE user_id = %s AND end_time IS NULL ORDER BY start_time DESC LIMIT 1",
                                    (user_id,)
                                )
                                session = cursor.fetchone()
                                if session:
                                    current_session_id = session[0]
                            if current_session_id:
                                cursor.execute(
                                    "INSERT INTO force_measurements (user_id, force_value, session_id) VALUES (%s, %s, %s)",
                                    (user_id, value_kg, current_session_id)
                                )
                                conn.commit()
                                print(f"Force measurement stored for session {current_session_id}")
                            else:
                                print("No active session to store force measurement.")
                        except Error as e:
                            print(f"Error storing data: {e}")
                            conn.rollback()
                        finally:
                            cursor.close()
                            conn.close()
                    else:
                        print("Failed to establish database connection")  # Debug log
            if json_data.get('type') == 'device_status':
                status = json_data.get('status')
                user_id = json_data.get('user_id', 1)
                # Call the same logic as /api/device-status
                await update_device_status(DeviceStatus(status=status, user_id=user_id))
            if json_data.get('type') == 'step':
                print("[DEBUG] Step data received:", json_data)
                user_id = json_data.get('user_id', 1)
                timestamp = datetime.fromtimestamp(json_data.get('timestamp') / 1000.0)
                peak_force = json_data.get('peak_force')
                gait_speed = json_data.get('gait_speed')
                accel_profile = json_data.get('accelProfile')
                # Find current session
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        if not current_session_id:
                            cursor.execute(
                                "SELECT id FROM sessions WHERE user_id = %s AND end_time IS NULL ORDER BY start_time DESC LIMIT 1",
                                (user_id,)
                            )
                            session = cursor.fetchone()
                            if session:
                                current_session_id = session[0]
                        if current_session_id:
                            print("peak_force:", peak_force, "gait_speed:", gait_speed)
                            cursor.execute(
                                "INSERT INTO steps (user_id, session_id, timestamp, peak_force, gait_speed, accel_profile) VALUES (%s, %s, %s, %s, %s, %s)",
                                (user_id, current_session_id, timestamp, peak_force, gait_speed, accel_profile)
                            )
                            conn.commit()
                            print(f"[DEBUG] Step inserted for session {current_session_id}, user {user_id}")
                    except Error as e:
                        print(f"Error storing step data: {e}")
                        conn.rollback()
                    finally:
                        cursor.close()
                        conn.close()
            if json_data.get('type') == 'posture_alert':
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        now = datetime.now()
                        cursor.execute(
                            "INSERT INTO posture_alerts (user_id, session_id, timestamp, anomaly, value) VALUES (%s, %s, %s, %s, %s)",
                            (json_data['user_id'], current_session_id, now, json_data['anomaly'], json_data['value'])
                        )
                        conn.commit()
                    except Error as e:
                        print(f"Error storing posture alert: {e}")
                        conn.rollback()
                    finally:
                        cursor.close()
                        conn.close()
            for connection in active_connections:
                if connection != websocket:
                    try:
                        await connection.send_text(data)
                        print(f"Broadcasted data to client: {connection.client}")  # Debug log
                    except Exception as e:
                        print(f"Error broadcasting to client {connection.client}: {e}")
    except WebSocketDisconnect:
        print(f"Client disconnected: {websocket.client}")  # Debug log
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

@app.get("/api/force-data")
async def get_force_data(user_id: int, limit: int = 100):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT force_value, timestamp FROM force_measurements WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s",
            (user_id, limit)
        )
        data = cursor.fetchall()
        return data
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/posture-alerts/{session_id}")
async def get_posture_alerts(session_id: int, user_id: int = Query(...)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT timestamp, anomaly, value FROM posture_alerts WHERE user_id = %s AND session_id = %s ORDER BY timestamp",
            (user_id, session_id)
        )
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

@app.post("/api/force-threshold")
async def set_force_threshold(threshold: float = Body(...)):
    global current_force_threshold
    current_force_threshold = threshold
    # Broadcast to all connected ESP32s
    message = {"type": "set_force_threshold", "threshold": threshold}
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            print(f"Error sending threshold to websocket {connection.client}: {e}")
    return {"message": "Threshold updated and sent to device"}

@app.post("/api/suggestion")
async def get_walking_suggestion(user_id: int = Form(...)):
    print(f"Received suggestion request for user_id={user_id}")
    # Fetch the most recent session for the user
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM sessions WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,))
    session = cursor.fetchone()
    if not session:
        return {"suggestion": "No session found for user."}
    session_id = session['id']
    # Fetch the last 3 steps
    cursor.execute("SELECT * FROM steps WHERE session_id=%s ORDER BY timestamp DESC LIMIT 3", (session_id,))
    steps = cursor.fetchall()
    conn.close()
    if len(steps) < 3:
        return {"suggestion": "Not enough step data for suggestion."}
    # Prepare data for AI
    steps = list(reversed(steps))  # Oldest first
    for i in range(3):
        if i == 0:
            steps[i]['duration'] = (steps[i+1]['timestamp'] - steps[i]['timestamp']).total_seconds()
        else:
            steps[i]['duration'] = (steps[i]['timestamp'] - steps[i-1]['timestamp']).total_seconds()
    api_key = GEMINI_API_KEY
    if not api_key:
        return {"suggestion": "Gemini API key not set on server."}
    try:
        suggestion = get_suggestion(steps[2], steps[1], steps[0], api_key)
        return {"suggestion": suggestion}
    except Exception as e:
        return {"suggestion": f"Error generating suggestion: {e}"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # print to console
    print(f"❌ Validation error for {request.url}: {exc.errors()} -- body={exc.body}")
    # return a JSON response so your browser/JS can see it too
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
