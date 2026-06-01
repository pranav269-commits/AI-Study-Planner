# app.py
# CFAI Smart Study Planner — modular Streamlit entry point.

import streamlit as st

st.set_page_config(
    page_title="CFAI Study Planner — KLH University",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .s-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .s-card-blue  { border-left: 4px solid #2196F3; background: #e8f4fd; }
    .s-card-green { border-left: 4px solid #4CAF50; background: #e8f5e9; }
    .s-card-orange{ border-left: 4px solid #FF9800; background: #fff3e0; }
    .s-card-red   { border-left: 4px solid #F44336; background: #ffebee; }
    .top-banner {
        background: #1a1a2e;
        color: white;
        padding: 22px 28px;
        border-radius: 10px;
        margin-bottom: 22px;
    }
    .top-banner h1 { margin: 0; font-size: 1.9em; }
    .top-banner p  { margin: 6px 0 0 0; color: #aaa; font-size: 0.95em; }
    .feat-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 14px;
        margin: 6px 0;
        background: #fafafa;
    }
    .feat-card strong { font-size: 1em; }
    .feat-card span   { color: #555; font-size: 0.88em; }
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82em;
        font-weight: 600;
    }
    [data-testid="stSidebar"] { padding-top: 0; }
    .stRadio label { font-size: 0.92em; }
</style>
""", unsafe_allow_html=True)

from modules.state import init_session, get_user, go
from modules.pages import (
    page_landing, page_signup, page_login, page_dashboard, page_study_planner,
    page_syllabus, page_progress, page_quiz, page_recommendation,
    page_exam_readiness, page_notes, page_algorithm_visualizer, page_csp_timetable,
    page_revision, page_admin, page_limitations
)


def show_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="background:#1a1a2e;color:white;padding:14px;border-radius:8px;text-align:center;margin-bottom:12px;">
            <div style="font-weight:bold;font-size:1em;">KLH University</div>
            <div style="font-size:0.8em;color:#aaa;">CFAI Study Planner</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.is_admin:
            st.write("Logged in as **Admin**")
        else:
            user = get_user()
            if user:
                st.write(f"**{user['name']}**")
                st.write(f"Roll: {user['roll']}")

        st.markdown("---")

        if not st.session_state.is_admin:
            nav_items = [
                ("dashboard", "Main Dashboard"),
                ("planner", "Study Planner"),
                ("syllabus", "Syllabus"),
                ("progress", "Progress Tracking"),
                ("quiz", "Quiz"),
                ("recommendation", "Recommendations"),
                ("readiness", "Exam Readiness"),
                ("notes", "Notes"),
                ("visualizer", "Algorithm Visualizer"),
                ("csp", "CSP Timetable"),
                ("revision", "Revision Plan"),
                ("limitations", "Limitations"),
            ]
            for key, label in nav_items:
                active = st.session_state.page == key
                btn_type = "primary" if active else "secondary"
                if st.button(label, use_container_width=True, key=f"nav_{key}", type=btn_type):
                    go(key)
        else:
            if st.button("Admin Dashboard", use_container_width=True, type="primary"):
                go("admin")

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.is_admin = False
            st.session_state.current_user = None
            st.session_state.quiz_active = False
            go("landing")


def main():
    init_session()

    if not st.session_state.logged_in:
        page = st.session_state.page
        if page == "signup":
            page_signup()
        elif page == "login":
            page_login()
        else:
            page_landing()
        return

    show_sidebar()

    if st.session_state.is_admin:
        page_admin()
        return

    page_map = {
        "dashboard": page_dashboard,
        "planner": page_study_planner,
        "syllabus": page_syllabus,
        "progress": page_progress,
        "quiz": page_quiz,
        "recommendation": page_recommendation,
        "readiness": page_exam_readiness,
        "notes": page_notes,
        "visualizer": page_algorithm_visualizer,
        "csp": page_csp_timetable,
        "revision": page_revision,
        "limitations": page_limitations,
    }

    current_page = st.session_state.get("page", "dashboard")
    render_fn = page_map.get(current_page, page_dashboard)
    render_fn()


if __name__ == "__main__":
    main()
