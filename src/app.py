"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

TEACHER_SESSION_COOKIE = "teacher_session"
TEACHER_SESSION_MAX_AGE = 8 * 60 * 60


class LoginRequest(BaseModel):
    username: str
    password: str


def _teacher_configuration() -> tuple[str, str, str] | None:
    username = os.getenv("TEACHER_USERNAME")
    password = os.getenv("TEACHER_PASSWORD")
    session_secret = os.getenv("SESSION_SECRET")
    if not username or not password or not session_secret:
        return None
    return username, password, session_secret


def _create_session_token(username: str, session_secret: str) -> str:
    payload = json.dumps(
        {"username": username, "expires_at": int(time.time()) + TEACHER_SESSION_MAX_AGE},
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(
        session_secret.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def _is_valid_teacher_session(token: str | None, username: str, session_secret: str) -> bool:
    if not token:
        return False

    try:
        encoded_payload, signature = token.split(".", 1)
        expected_signature = hmac.new(
            session_secret.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return False

        padding = "=" * (-len(encoded_payload) % 4)
        payload: Any = json.loads(
            base64.urlsafe_b64decode(encoded_payload + padding).decode("utf-8")
        )
    except (ValueError, UnicodeDecodeError):
        return False

    return (
        isinstance(payload, dict)
        and payload.get("username") == username
        and isinstance(payload.get("expires_at"), int)
        and payload["expires_at"] > int(time.time())
    )


def _require_teacher(request: Request) -> tuple[str, str]:
    configuration = _teacher_configuration()
    if configuration is None:
        raise HTTPException(status_code=503, detail="Teacher login is not configured")
    username, _, session_secret = configuration
    token = request.cookies.get(TEACHER_SESSION_COOKIE)
    if not _is_valid_teacher_session(token, username, session_secret):
        raise HTTPException(status_code=401, detail="Teacher login required")
    return username, session_secret


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

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


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.get("/auth/status")
def get_auth_status(request: Request):
    configuration = _teacher_configuration()
    if configuration is None:
        return {"authenticated": False}
    username, _, session_secret = configuration
    token = request.cookies.get(TEACHER_SESSION_COOKIE)
    return {
        "authenticated": _is_valid_teacher_session(token, username, session_secret)
    }


@app.post("/auth/login")
def login(credentials: LoginRequest, request: Request, response: Response):
    configuration = _teacher_configuration()
    if configuration is None:
        raise HTTPException(status_code=503, detail="Teacher login is not configured")

    username, password, session_secret = configuration
    valid_username = hmac.compare_digest(
        credentials.username.encode("utf-8"), username.encode("utf-8")
    )
    valid_password = hmac.compare_digest(
        credentials.password.encode("utf-8"), password.encode("utf-8")
    )
    if not (valid_username and valid_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key=TEACHER_SESSION_COOKIE,
        value=_create_session_token(username, session_secret),
        max_age=TEACHER_SESSION_MAX_AGE,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    return {"message": "Teacher login successful"}


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    _require_teacher(request)
    response.delete_cookie(
        key=TEACHER_SESSION_COOKIE,
        path="/",
        secure=request.url.scheme == "https",
        httponly=True,
        samesite="strict",
    )
    return {"message": "Teacher logout successful"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, request: Request):
    """Sign up a student for an activity"""
    _require_teacher(request)

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
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, request: Request):
    """Unregister a student from an activity"""
    _require_teacher(request)

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
    return {"message": f"Unregistered {email} from {activity_name}"}
