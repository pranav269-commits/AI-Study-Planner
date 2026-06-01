# modules/state.py
# Session-state helpers for login, user storage, and navigation.

import streamlit as st
from datetime import date, timedelta

def init_session():
    """Set up session_state defaults on first run."""
    defaults = {
        "logged_in": False,
        "is_admin": False,
        "current_user": None,
        "page": "landing",
        "quiz_active": False,
        "quiz_co": None,
        "quiz_submitted": False,
        "users": {
            # Demo student account so you can test without signing up
            "student@klh.edu": {
                "name": "Demo Student",
                "roll": "21BCE1234",
                "email": "student@klh.edu",
                "password": "student123",
                "semester": "6",
                "exam_date": str(date.today() + timedelta(days=30)),
                "daily_hours": 3,
                "level": "Average",
                "completed_topics": {},
                "quiz_scores": {},
                "study_plan": [],
            }
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def get_user():
    """Return the current student's data dict, or None."""
    if st.session_state.current_user:
        return st.session_state.users.get(st.session_state.current_user)
    return None

def save_user(data):
    """Write updated data back into session_state."""
    if st.session_state.current_user:
        st.session_state.users[st.session_state.current_user] = data

def go(page):
    """Navigate to a page and rerun."""
    st.session_state.page = page
    st.rerun()

