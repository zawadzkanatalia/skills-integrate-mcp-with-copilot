"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

BASE_DIR = Path(__file__).resolve().parent
TEACHERS_FILE = BASE_DIR / "teachers.json"


def load_teachers() -> dict[str, str]:
    if TEACHERS_FILE.exists():
        with TEACHERS_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return {"teacher": "password123"}


def save_teachers() -> None:
    with TEACHERS_FILE.open("w", encoding="utf-8") as fh:
        json.dump(teachers, fh, indent=2)


teachers = load_teachers()

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def get_current_user(request: Request) -> Optional[str]:
    username = request.cookies.get("teacher_session")
    if username and username in teachers:
        return username
    return None


def require_teacher(request: Request) -> str:
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=403, detail="Teacher login required")
    return username


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.get("/auth/me")
def get_auth_status(request: Request):
    username = get_current_user(request)
    return {"authenticated": username is not None, "username": username}


@app.post("/auth/login")
async def login(request: Request):
    payload: Optional[dict[str, Any]] = None
    try:
        payload = await request.json()
    except Exception:
        payload = None

    username = None
    password = None

    if payload:
        username = payload.get("username")
        password = payload.get("password")
    else:
        username = request.query_params.get("username")
        password = request.query_params.get("password")

    if isinstance(username, str) and isinstance(password, str) and teachers.get(username) == password:
        response = JSONResponse({"message": f"Welcome, {username}", "authenticated": True})
        response.set_cookie("teacher_session", username, httponly=True, samesite="lax")
        return response

    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/auth/logout")
def logout():
    response = JSONResponse({"message": "Logged out", "authenticated": False})
    response.delete_cookie("teacher_session")
    return response


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(request: Request, activity_name: str, email: str):
    """Sign up a student for an activity"""
    require_teacher(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}", "participants": activity["participants"]}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(request: Request, activity_name: str, email: str):
    """Unregister a student from an activity"""
    require_teacher(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}", "participants": activity["participants"]}
