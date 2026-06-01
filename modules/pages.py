# modules/pages.py
# All Streamlit page functions for the CFAI Smart Study Planner.

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta

from modules.data import (
    SYLLABUS, QUIZ_QUESTIONS, NOTES, GRAPH, HEURISTICS, GRAPH_NODES
)
from modules.state import get_user, save_user, go
from modules.utils import calculate_readiness, generate_study_plan
from modules.algorithms import bfs, dfs, ucs, greedy, astar
from modules.graph_utils import draw_graph

def page_landing():
    st.markdown("""
    <div class="top-banner">
        <div style="font-size:0.9em;color:#aaa;margin-bottom:6px;">KLH University — Department of Computer Science and Engineering</div>
        <h1>CFAI Smart Study Planner</h1>
        <p>A Python-based study assistant for CO1 to CO6 preparation &nbsp;|&nbsp; B.Tech CSE</p>
    </div>
    """, unsafe_allow_html=True)

    st.write(
        "This is a college project built for students preparing the CFAI (Computational Foundations of "
        "Artificial Intelligence) course. It helps you plan your study sessions, track your syllabus "
        "progress, take quizzes, visualize search algorithms, and estimate your exam readiness."
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Login", use_container_width=True, type="primary"):
            go("login")
    with col2:
        if st.button("Sign Up", use_container_width=True):
            go("signup")
    with col3:
        if st.button("Quick Demo (skip login)", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.is_admin = False
            st.session_state.current_user = "student@klh.edu"
            go("dashboard")

    st.markdown("---")
    st.subheader("What's inside")

    features = [
        ("Study Planner", "Generates a day-wise schedule based on your exam date, daily hours, and topic difficulty."),
        ("Syllabus Tracker", "Track your CO1–CO6 progress topic by topic and mark completed ones."),
        ("Quiz System", "MCQ quiz for each CO. See your score, correct answers, and what to revise."),
        ("Recommendations", "Suggests the next topic to study using a simple priority formula."),
        ("Exam Readiness", "Estimates how prepared you are based on completion, quiz scores, and time left."),
        ("Algorithm Visualizer", "Step-by-step BFS, DFS, UCS, Greedy, and A* on a sample graph."),
        ("CSP Timetable", "Generates a timetable using constraint satisfaction logic (CO3 demo)."),
        ("Notes", "Quick-reference notes for every important CFAI topic."),
    ]

    cols = st.columns(2)
    for i, (title, desc) in enumerate(features):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="feat-card">
                <strong>{title}</strong><br>
                <span>{desc}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "<p style='color:#888;font-size:0.82em;text-align:center;'>"
        "KLH University &nbsp;|&nbsp; CFAI Project &nbsp;|&nbsp; Built with Python and Streamlit"
        "</p>",
        unsafe_allow_html=True,
    )

def page_signup():
    st.title("Create Account")
    st.write("Fill in your details below.")

    with st.form("signup_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name")
            roll = st.text_input("Roll Number")
            email = st.text_input("Email")
        with c2:
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            semester = st.selectbox("Semester", [str(i) for i in range(1, 9)])

        c3, c4 = st.columns(2)
        with c3:
            exam_date = st.date_input(
                "Exam Date",
                value=date.today() + timedelta(days=30),
                min_value=date.today(),
            )
            daily_hours = st.slider("Daily Study Hours", 1, 10, 3)
        with c4:
            level = st.selectbox(
                "Current Preparation Level",
                ["Beginner", "Average", "Good", "Revision Stage"],
            )

        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if not all([name, roll, email, password]):
            st.error("Please fill in all fields.")
        elif password != confirm:
            st.error("Passwords do not match.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        elif email in st.session_state.users:
            st.error("An account with this email already exists.")
        else:
            st.session_state.users[email] = {
                "name": name,
                "roll": roll,
                "email": email,
                "password": password,
                "semester": semester,
                "exam_date": str(exam_date),
                "daily_hours": daily_hours,
                "level": level,
                "completed_topics": {},
                "quiz_scores": {},
                "study_plan": [],
            }
            st.success(f"Account created for {name}. Please log in.")
            go("login")

    if st.button("Back to Home"):
        go("landing")

def page_login():
    st.title("Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        if email == "admin@klh.edu" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.is_admin = True
            st.session_state.current_user = None
            go("admin")
        elif email in st.session_state.users:
            if st.session_state.users[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.is_admin = False
                st.session_state.current_user = email
                go("dashboard")
            else:
                st.error("Incorrect password.")
        else:
            st.error("No account found with this email.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Create Account", use_container_width=True):
            go("signup")
    with c2:
        if st.button("Back to Home", use_container_width=True):
            go("landing")

    st.info("Demo: student@klh.edu / student123  |  Admin: admin@klh.edu / admin123")

def page_dashboard():
    user = get_user()
    r = calculate_readiness(user)
    completed = user.get("completed_topics", {})
    quiz_scores = user.get("quiz_scores", {})

    st.markdown(f"""
    <div class="top-banner">
        <h1>Welcome back, {user['name']}</h1>
        <p>Roll No: {user['roll']} &nbsp;|&nbsp; Semester {user['semester']} &nbsp;|&nbsp;
           Exam in <strong>{r['days_left']}</strong> days &nbsp;|&nbsp; Level: {user['level']}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Syllabus Done", f"{r['comp_pct']}%")
    col2.metric("Topics Completed", f"{r['done']}/{r['total']}")
    col3.metric("Quiz Average", f"{r['quiz_avg']:.0f}%")
    col4.metric("Exam Readiness", f"{r['readiness']}%")

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("CO-wise Progress")
        for co, info in SYLLABUS.items():
            total = len(info["topics"])
            done = len(completed.get(co, []))
            pct = int(done / total * 100) if total else 0
            st.write(f"**{co}** — {info['title']}")
            st.progress(pct / 100, text=f"{done}/{total} topics ({pct}%)")

    with c2:
        st.subheader("Summary")

        # Weakest CO (lowest quiz score or not attempted)
        all_cos = list(SYLLABUS.keys())
        weak_co = min(all_cos, key=lambda c: quiz_scores.get(c, 50))
        strong_co = max(all_cos, key=lambda c: quiz_scores.get(c, 50))
        weak_score = quiz_scores.get(weak_co, None)
        strong_score = quiz_scores.get(strong_co, None)

        st.markdown(f"""
        <div class="s-card s-card-blue">
            <b>Weakest Area:</b> {weak_co} — {SYLLABUS[weak_co]['title']}<br>
            Quiz score: {f"{weak_score:.0f}%" if weak_score is not None else "Not taken yet"}
        </div>
        <div class="s-card s-card-green">
            <b>Strongest Area:</b> {strong_co} — {SYLLABUS[strong_co]['title']}<br>
            Quiz score: {f"{strong_score:.0f}%" if strong_score is not None else "Not taken yet"}
        </div>
        """, unsafe_allow_html=True)

        # Next pending topic
        st.subheader("What to study next")
        found = False
        for co, info in SYLLABUS.items():
            comp = completed.get(co, [])
            for topic in info["topics"]:
                if topic not in comp:
                    st.info(f"**{topic}** ({co})")
                    found = True
                    break
            if found:
                break
        if not found:
            st.success("All topics completed!")

    st.markdown("---")
    st.subheader("How this project maps to CFAI concepts")
    st.markdown("""
| CFAI Concept | Used in this project |
|---|---|
| Agent model, PEAS (CO1) | The recommendation system acts like an agent with a performance measure (priority score) |
| Search algorithms (CO2) | Algorithm Visualizer runs BFS, DFS, UCS, Greedy, and A* on a sample graph |
| CSP and backtracking (CO3) | CSP Timetable Generator uses constraint logic to assign topics to days |
| Utility functions, decisions (CO4) | Priority Score formula (Difficulty + Importance + Weakness) drives recommendations |
| Probability, uncertainty (CO5) | Exam readiness is a weighted estimate that reflects uncertainty in preparation |
| Hybrid AI, explainability (CO6) | Recommendations include plain-language reasons; limitations are clearly documented |
    """)

def page_study_planner():
    user = get_user()
    st.title("Study Planner")
    st.write(
        "Generates a personalised day-wise study schedule. "
        "Topics are prioritised by difficulty, exam importance, and your quiz performance."
    )

    try:
        exam_dt = datetime.strptime(user["exam_date"], "%Y-%m-%d").date()
        days_left = (exam_dt - date.today()).days
    except Exception:
        days_left = 30

    c1, c2, c3 = st.columns(3)
    c1.write(f"**Exam Date:** {user['exam_date']}")
    c2.write(f"**Daily Hours:** {user['daily_hours']}")
    c3.write(f"**Days Left:** {days_left}")

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Generate Study Plan", type="primary", use_container_width=True):
            user["study_plan"] = generate_study_plan(user)
            save_user(user)
            st.success("Plan generated.")
            st.rerun()
    with b2:
        if st.button("Reschedule Pending", use_container_width=True):
            user["study_plan"] = generate_study_plan(user)
            save_user(user)
            st.info("Rescheduled.")
            st.rerun()
    with b3:
        if st.button("Reset Plan", use_container_width=True):
            user["study_plan"] = []
            save_user(user)
            st.rerun()

    plan = user.get("study_plan", [])
    if not plan:
        st.info("No study plan yet. Click 'Generate Study Plan' to create one.")
        return

    df = pd.DataFrame(plan)

    st.markdown("---")
    st.subheader("Mark a Topic as Completed")
    pending_topics = [r["Topic"] for r in plan if r["Status"] == "Pending" and not r["Topic"].startswith("[REVISION]")]
    if pending_topics:
        sel = st.selectbox("Select topic:", pending_topics)
        sel_co = next((r["CO"] for r in plan if r["Topic"] == sel), None)
        if st.button("Mark as Completed"):
            # Update completed_topics
            comp = user.get("completed_topics", {})
            if sel_co and sel_co != "All":
                if sel_co not in comp:
                    comp[sel_co] = []
                if sel not in comp[sel_co]:
                    comp[sel_co].append(sel)
            user["completed_topics"] = comp
            # Update plan status
            for row in user["study_plan"]:
                if row["Topic"] == sel:
                    row["Status"] = "Completed"
                    break
            save_user(user)
            st.success(f"'{sel}' marked as completed!")
            st.rerun()

    st.markdown("---")
    st.subheader("Your Study Plan")

    total_rows = len(df)
    pending_count = len(df[df["Status"] == "Pending"])
    done_count = len(df[df["Status"] == "Completed"])
    st.write(f"Total: {total_rows} &nbsp;|&nbsp; Pending: {pending_count} &nbsp;|&nbsp; Completed: {done_count}")

    status_filter = st.multiselect("Filter by status:", ["Pending", "Completed"], default=["Pending", "Completed"])
    co_filter = st.multiselect("Filter by CO:", list(SYLLABUS.keys()) + ["All"], default=list(SYLLABUS.keys()) + ["All"])

    filtered = df[df["Status"].isin(status_filter) & df["CO"].isin(co_filter)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

def page_syllabus():
    user = get_user()
    completed = user.get("completed_topics", {})

    st.title("CFAI Syllabus")
    st.write("CO1 to CO6 topics. Expand any CO to see topics and mark them as completed.")

    for co, info in SYLLABUS.items():
        comp = completed.get(co, [])
        total = len(info["topics"])
        done = len(comp)
        pct = int(done / total * 100) if total else 0

        with st.expander(f"{co} — {info['title']}  ({done}/{total} done)", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Difficulty:** {info['difficulty']}")
            c2.write(f"**Importance:** {info['importance']}")
            c3.write(f"**Progress:** {pct}%")
            st.progress(pct / 100)

            st.write("**Topics:**")
            for topic in info["topics"]:
                if topic in comp:
                    st.markdown(f"<span style='color:green'>✓ {topic}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:#555'>○ {topic}</span>", unsafe_allow_html=True)

            pending = [t for t in info["topics"] if t not in comp]
            if pending:
                sel = st.selectbox(f"Mark topic as done ({co}):", ["-- select --"] + pending, key=f"syl_{co}")
                if st.button(f"Mark Done", key=f"btn_{co}"):
                    if sel != "-- select --":
                        if co not in completed:
                            completed[co] = []
                        completed[co].append(sel)
                        user["completed_topics"] = completed
                        save_user(user)
                        st.success(f"'{sel}' marked as completed!")
                        st.rerun()
            else:
                st.success("All topics in this CO are done!")

def page_progress():
    user = get_user()
    completed = user.get("completed_topics", {})
    quiz_scores = user.get("quiz_scores", {})

    st.title("Progress Tracking")

    total = sum(len(SYLLABUS[co]["topics"]) for co in SYLLABUS)
    done = sum(len(completed.get(co, [])) for co in SYLLABUS)
    pct = int(done / total * 100) if total else 0

    st.subheader("Overall Syllabus Progress")
    st.progress(pct / 100, text=f"{done} of {total} topics done ({pct}%)")

    c1, c2, c3 = st.columns(3)
    c1.metric("Completed", done)
    c2.metric("Remaining", total - done)
    avg = sum(quiz_scores.values()) / len(quiz_scores) if quiz_scores else 0
    c3.metric("Quiz Average", f"{avg:.0f}%")

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("CO-wise Completion")
        for co, info in SYLLABUS.items():
            t = len(info["topics"])
            d = len(completed.get(co, []))
            p = int(d / t * 100) if t else 0
            st.write(f"**{co}** — {info['title']}")
            st.progress(p / 100, text=f"{d}/{t} ({p}%)")

    with c2:
        st.subheader("Quiz Scores by CO")
        for co in SYLLABUS:
            s = quiz_scores.get(co, None)
            if s is not None:
                color = "green" if s >= 70 else ("orange" if s >= 40 else "red")
                st.markdown(f"**{co}:** <span style='color:{color}'>{s:.0f}%</span>", unsafe_allow_html=True)
                st.progress(s / 100)
            else:
                st.write(f"**{co}:** Not attempted yet")

    st.markdown("---")
    st.subheader("CO-wise Completion Chart")

    cos = list(SYLLABUS.keys())
    comp_pcts = [
        int(len(completed.get(co, [])) / len(SYLLABUS[co]["topics"]) * 100)
        for co in cos
    ]
    bar_colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336", "#00BCD4"]

    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(cos, comp_pcts, color=bar_colors, width=0.55)
    ax.set_ylabel("Completion (%)")
    ax.set_title("Syllabus Completion by CO")
    ax.set_ylim(0, 115)
    for b, v in zip(bars, comp_pcts):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, f"{v}%", ha="center", va="bottom", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    st.pyplot(fig)
    plt.close()

    if quiz_scores:
        st.subheader("Quiz Score Chart")
        qs_cos = list(quiz_scores.keys())
        qs_vals = list(quiz_scores.values())
        qs_colors = ["green" if v >= 70 else ("orange" if v >= 40 else "red") for v in qs_vals]

        fig2, ax2 = plt.subplots(figsize=(9, 4))
        ax2.bar(qs_cos, qs_vals, color=qs_colors, width=0.55)
        ax2.axhline(70, color="green", linestyle="--", alpha=0.6, label="Good (70%)")
        ax2.axhline(40, color="orange", linestyle="--", alpha=0.6, label="Average (40%)")
        ax2.set_ylabel("Score (%)")
        ax2.set_title("Quiz Scores by CO")
        ax2.set_ylim(0, 115)
        ax2.legend(fontsize=8)
        ax2.spines[["top", "right"]].set_visible(False)
        st.pyplot(fig2)
        plt.close()

def page_quiz():
    user = get_user()
    st.title("Quiz")
    st.write("Select a CO and answer the MCQ questions. Results show correct answers and what to revise.")

    # ── Quiz selection screen ──────────────────────────────────────────────
    if not st.session_state.quiz_active:
        st.subheader("Choose a CO to test yourself:")
        quiz_scores = user.get("quiz_scores", {})
        cols = st.columns(3)
        for i, co in enumerate(SYLLABUS):
            with cols[i % 3]:
                s = quiz_scores.get(co, None)
                label = f"{co}\n{SYLLABUS[co]['title']}\n{f'Last: {s:.0f}%' if s else 'Not attempted'}"
                if st.button(label, use_container_width=True, key=f"start_{co}"):
                    st.session_state.quiz_active = True
                    st.session_state.quiz_co = co
                    st.session_state.quiz_submitted = False
                    # Clear previous answers from session state
                    for k in list(st.session_state.keys()):
                        if k.startswith("qa_"):
                            del st.session_state[k]
                    st.rerun()
        return

    # ── Quiz in progress ───────────────────────────────────────────────────
    co = st.session_state.quiz_co
    questions = QUIZ_QUESTIONS.get(co, [])

    st.subheader(f"Quiz: {co} — {SYLLABUS[co]['title']}")
    st.write(f"{len(questions)} questions")

    if not st.session_state.quiz_submitted:
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i + 1}: {q['q']}**")
            st.radio(
                "",
                q["options"],
                key=f"qa_{co}_{i}",
                index=None,
                label_visibility="collapsed",
            )
            st.write("")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Submit Quiz", type="primary", use_container_width=True):
                # Check all answered
                unanswered = [i for i in range(len(questions)) if st.session_state.get(f"qa_{co}_{i}") is None]
                if unanswered:
                    st.warning(f"Please answer all questions. Unanswered: Q{[u+1 for u in unanswered]}")
                else:
                    st.session_state.quiz_submitted = True
                    st.rerun()
        with c2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.quiz_active = False
                st.rerun()

    else:
        # ── Results ────────────────────────────────────────────────────────
        correct = 0
        wrong_topics = []
        results = []

        for i, q in enumerate(questions):
            ans_text = st.session_state.get(f"qa_{co}_{i}", None)
            user_idx = q["options"].index(ans_text) if ans_text in q["options"] else -1
            is_ok = user_idx == q["answer"]
            if is_ok:
                correct += 1
            else:
                wrong_topics.append(q["topic"])
            results.append({"q": q, "user_idx": user_idx, "is_ok": is_ok})

        score_pct = correct / len(questions) * 100

        # Save score
        user_data = get_user()
        user_data["quiz_scores"][co] = score_pct
        save_user(user_data)

        score_color = "#4CAF50" if score_pct >= 70 else ("#FF9800" if score_pct >= 40 else "#F44336")
        st.markdown(f"""
        <div style="background:{score_color};color:white;padding:22px;border-radius:8px;text-align:center;margin-bottom:18px;">
            <h2 style="margin:0;">{correct} / {len(questions)} Correct — {score_pct:.0f}%</h2>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Question Review")
        for r in results:
            q = r["q"]
            bg = "#e8f5e9" if r["is_ok"] else "#ffebee"
            icon = "✓" if r["is_ok"] else "✗"
            user_ans = q["options"][r["user_idx"]] if r["user_idx"] >= 0 else "Not answered"
            st.markdown(f"""
            <div style="background:{bg};border-radius:6px;padding:12px;margin:6px 0;">
                <strong>{icon} {q['q']}</strong><br>
                Your answer: {user_ans}<br>
                Correct answer: <strong>{q['options'][q['answer']]}</strong>
            </div>
            """, unsafe_allow_html=True)

        if wrong_topics:
            st.subheader("Topics to Revise")
            for t in set(wrong_topics):
                st.write(f"- {t}")

        if st.button("Back to Quiz Selection", use_container_width=True):
            st.session_state.quiz_active = False
            st.session_state.quiz_submitted = False
            for k in list(st.session_state.keys()):
                if k.startswith("qa_"):
                    del st.session_state[k]
            st.rerun()

def page_recommendation():
    user = get_user()
    completed = user.get("completed_topics", {})
    quiz_scores = user.get("quiz_scores", {})

    st.title("Recommendations")
    st.write(
        "The next topic to study is suggested using a simple priority formula. "
        "This is rule-based logic, not machine learning — it mimics utility-based decision making from CO4."
    )

    with st.expander("How the formula works"):
        st.write(
            "**Priority Score = Difficulty + Importance + (Weakness × 3) − Confidence**\n\n"
            "- Difficulty: Medium=2, Hard=3, Very Hard=4\n"
            "- Importance: High=3, Very High=4\n"
            "- Weakness: (100 − quiz_score) / 100  (higher score = lower weakness)\n"
            "- Confidence: quiz_score / 100\n\n"
            "Higher priority score → study this topic sooner."
        )

    recs = []
    for co, info in SYLLABUS.items():
        comp = completed.get(co, [])
        qs = quiz_scores.get(co, 50)
        weakness = max(0, (100 - qs) / 100)
        confidence = qs / 100
        diff_val = {"Medium": 2, "Hard": 3, "Very Hard": 4}.get(info["difficulty"], 2)
        imp_val = {"High": 3, "Very High": 4}.get(info["importance"], 3)

        for topic in info["topics"]:
            if topic not in comp:
                score = diff_val + imp_val + weakness * 3 - confidence
                parts = []
                if qs < 50:
                    parts.append(f"your {co} quiz score is low ({qs:.0f}%)")
                if info["difficulty"] in ["Hard", "Very Hard"]:
                    parts.append(f"it is a {info['difficulty'].lower()} topic")
                if info["importance"] == "Very High":
                    parts.append("it is very important for the exam")
                parts.append("it has not been completed yet")
                reason = "Recommended because " + ", ".join(parts) + "."

                recs.append(
                    {
                        "CO": co,
                        "Topic": topic,
                        "Priority Score": round(score, 2),
                        "Difficulty": info["difficulty"],
                        "Importance": info["importance"],
                        "Reason": reason,
                    }
                )

    if not recs:
        st.success("You have completed all topics. Well done!")
        return

    recs.sort(key=lambda x: -x["Priority Score"])

    top = recs[0]
    st.subheader("Top Recommendation Right Now")
    st.markdown(f"""
    <div class="s-card s-card-blue" style="padding:20px;">
        <h3 style="margin:0 0 6px 0;">{top['Topic']}</h3>
        <div style="color:#555;margin-bottom:8px;">{top['CO']} &nbsp;|&nbsp; Difficulty: {top['Difficulty']} &nbsp;|&nbsp; Importance: {top['Importance']}</div>
        <div><strong>Priority Score: {top['Priority Score']}</strong></div>
        <div style="margin-top:8px;font-style:italic;color:#444;">{top['Reason']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Top 2 Recommendations per CO")
    for co in SYLLABUS:
        co_recs = [r for r in recs if r["CO"] == co][:2]
        if co_recs:
            with st.expander(f"{co} — {SYLLABUS[co]['title']}"):
                for r in co_recs:
                    st.markdown(f"**{r['Topic']}** (Score: {r['Priority Score']})")
                    st.markdown(f"*{r['Reason']}*")
                    st.markdown("---")

    st.subheader("All Pending Topics Ranked")
    df = pd.DataFrame(recs)[["CO", "Topic", "Priority Score", "Difficulty", "Importance"]]
    st.dataframe(df.head(20), use_container_width=True, hide_index=True)

def page_exam_readiness():
    user = get_user()
    r = calculate_readiness(user)
    quiz_scores = user.get("quiz_scores", {})
    completed = user.get("completed_topics", {})

    st.title("Exam Readiness")
    st.write(
        "This is an estimate based on your syllabus completion, quiz scores, and time remaining. "
        "It is not a guarantee of exam performance."
    )

    pct = r["readiness"]

    if pct <= 40:
        status, color = "Not Ready", "#F44336"
        suggestion = "You need significant effort. Start with high-priority topics and take at least one quiz per CO."
    elif pct <= 70:
        status, color = "Needs More Revision", "#FF9800"
        suggestion = "You have some preparation done but need to cover weak areas and retake quizzes."
    elif pct <= 90:
        status, color = "Good Preparation", "#4CAF50"
        suggestion = "You are well-prepared. Focus the remaining time on your weakest COs and do a final revision."
    else:
        status, color = "Exam Ready", "#2196F3"
        suggestion = "Excellent preparation. Review your notes and stay calm before the exam."

    st.markdown(f"""
    <div style="background:{color};color:white;padding:30px;border-radius:10px;text-align:center;margin-bottom:20px;">
        <div style="font-size:3.5em;font-weight:bold;margin:0;">{pct}%</div>
        <div style="font-size:1.4em;margin-top:8px;">{status}</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Syllabus Done", f"{r['comp_pct']}%")
    c2.metric("Quiz Average", f"{r['quiz_avg']:.0f}%")
    c3.metric("Days Left", r["days_left"])
    c4.metric("Topics Done", f"{r['done']}/{r['total']}")

    st.info(suggestion)

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Weak Areas (quiz < 60%)")
        found = False
        for co in SYLLABUS:
            s = quiz_scores.get(co, None)
            if s is None or s < 60:
                tag = f"{s:.0f}% quiz" if s is not None else "quiz not taken"
                st.write(f"- **{co}** ({tag})")
                found = True
        if not found:
            st.write("No weak areas found — all quiz scores are above 60%!")

    with c2:
        st.subheader("Strong Areas (quiz ≥ 70%)")
        found = False
        for co in SYLLABUS:
            s = quiz_scores.get(co, None)
            if s is not None and s >= 70:
                st.write(f"- **{co}** ({s:.0f}%)")
                found = True
        if not found:
            st.write("No strong areas identified yet. Take quizzes to see your strengths.")

    st.markdown("---")
    st.subheader("Readiness Breakdown Chart")
    cats = ["Syllabus\nCompletion", "Quiz\nAverage", "Time\nFactor", "Overall\nReadiness"]
    vals = [r["comp_pct"], r["quiz_avg"], r["time_score"], pct]
    colors = ["#2196F3", "#4CAF50", "#FF9800", color]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(cats, vals, color=colors, width=0.5)
    ax.set_ylim(0, 120)
    ax.set_ylabel("Score (%)")
    ax.set_title("Exam Readiness Breakdown")
    ax.spines[["top", "right"]].set_visible(False)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, f"{v:.0f}%", ha="center", va="bottom")
    st.pyplot(fig)
    plt.close()

    st.markdown("---")
    st.subheader("Suggested Focus for Final Revision")
    for co in SYLLABUS:
        s = quiz_scores.get(co, 0)
        if s < 60:
            comp = completed.get(co, [])
            pending = [t for t in SYLLABUS[co]["topics"] if t not in comp][:2]
            if pending:
                st.write(f"**{co}:** Focus on — {', '.join(pending)}")

    st.caption(
        "Note: Readiness is an estimate. Formula: 40% syllabus + 40% quiz average + 20% time factor. "
        "It does not predict actual exam performance."
    )

def page_notes():
    st.title("Study Notes")
    st.write("Quick-reference notes for all major CFAI topics. Useful for last-minute revision.")

    co_filter = st.selectbox("Filter by CO:", ["All"] + list(SYLLABUS.keys()))

    for topic, note in NOTES.items():
        if co_filter != "All" and note["co"] != co_filter:
            continue
        with st.expander(f"{topic}  [{note['co']}]"):
            st.markdown(f"**Definition:**  {note['definition']}")
            st.markdown("**Key Points:**")
            for pt in note["key_points"]:
                st.write(f"- {pt}")
            st.markdown(f"**Example:**  {note['example']}")
            st.markdown(
                f"<div class='s-card s-card-orange' style='margin-top:8px;'>"
                f"<strong>Exam Hint:</strong> {note['exam_hint']}</div>",
                unsafe_allow_html=True,
            )

def page_algorithm_visualizer():
    st.title("Algorithm Visualizer")
    st.write(
        "Select an algorithm, a start node, and a goal node. "
        "The visualizer shows the order nodes were visited and the final path found."
    )

    st.subheader("Graph Details")
    st.markdown("""
**Nodes:** A, B, C, D, E, F, G  
**Edges and costs:** A–B:1, A–C:4, B–D:2, B–E:5, C–F:3, D–G:3, E–G:1, F–G:2  
**Heuristic h(n) to G:** A=6, B=4, C=5, D=2, E=1, F=3, G=0
    """)

    c1, c2, c3 = st.columns(3)
    with c1:
        algo = st.selectbox("Algorithm:", ["BFS", "DFS", "UCS", "Greedy Search", "A*"])
    with c2:
        start = st.selectbox("Start Node:", GRAPH_NODES, index=0)
    with c3:
        goal = st.selectbox("Goal Node:", GRAPH_NODES, index=len(GRAPH_NODES) - 1)

    algo_descriptions = {
        "BFS": "BFS explores level by level using a queue. It finds the fewest-hops path but does not consider edge weights.",
        "DFS": "DFS goes deep first using a stack. It is memory-efficient but not guaranteed to find the shortest path.",
        "UCS": "UCS expands the cheapest cumulative path. Optimal for weighted graphs. Uses a priority queue ordered by g(n).",
        "Greedy Search": "Greedy picks the node closest to the goal by heuristic h(n) only. Fast but may miss the optimal path.",
        "A*": "A* combines g(n) (actual cost) and h(n) (heuristic) as f(n) = g(n) + h(n). Optimal when heuristic is admissible.",
    }

    if st.button("Run", type="primary", use_container_width=True):
        if start == goal:
            st.warning("Start and goal are the same.")
            return

        if algo == "BFS":
            visited, path, cost = bfs(GRAPH, start, goal)
        elif algo == "DFS":
            visited, path, cost = dfs(GRAPH, start, goal)
        elif algo == "UCS":
            visited, path, cost = ucs(GRAPH, start, goal)
        elif algo == "Greedy Search":
            visited, path, cost = greedy(GRAPH, start, goal, HEURISTICS)
        else:
            visited, path, cost = astar(GRAPH, start, goal, HEURISTICS)

        st.markdown("---")

        c1, c2, c3 = st.columns(3)
        c1.metric("Nodes Visited", len(visited))
        c2.metric("Path", " → ".join(path) if path else "No path found")
        c3.metric("Total Cost", cost if cost != float("inf") else "—")

        st.info(f"**{algo}:** {algo_descriptions[algo]}")

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Visited Order")
            visit_df = pd.DataFrame({"Step": range(1, len(visited) + 1), "Node": visited})
            st.dataframe(visit_df, use_container_width=True, hide_index=True)

        with c2:
            if path and len(path) > 1:
                st.subheader("Path Details")
                path_rows = []
                for i in range(len(path) - 1):
                    path_rows.append({
                        "From": path[i],
                        "To": path[i + 1],
                        "Edge Cost": GRAPH[path[i]][path[i + 1]],
                        "h(To)": HEURISTICS.get(path[i + 1], 0),
                    })
                st.dataframe(pd.DataFrame(path_rows), use_container_width=True, hide_index=True)

        st.subheader("Graph")
        fig = draw_graph(visited, path if path else [], start, goal)
        fig.suptitle(f"{algo}: {start} → {goal}", fontsize=12, y=1.01)
        st.pyplot(fig)
        plt.close()

def page_csp_timetable():
    user = get_user()
    completed = user.get("completed_topics", {})
    quiz_scores = user.get("quiz_scores", {})

    st.title("CSP Timetable Generator")
    st.write(
        "Generates a study timetable using constraint satisfaction logic. "
        "This is a simplified demonstration of CO3 concepts — it is not a full backtracking CSP solver."
    )

    st.subheader("Constraints applied")
    st.markdown("""
- **C1:** Daily study hours must not exceed your set limit.
- **C2:** Two high-difficulty topics (Hard / Very Hard) cannot be on the same day.
- **C3:** Topics from weak COs (quiz score < 60%) appear twice for extra revision.
- **C4:** The last 3 days before the exam are reserved for revision.
- **C5:** All COs should be started before the exam date.
    """)

    try:
        exam_dt = datetime.strptime(user["exam_date"], "%Y-%m-%d").date()
        days_left = (exam_dt - date.today()).days
    except Exception:
        days_left = 0

    if days_left <= 0:
        st.error("Exam date has passed or is too close. Please update your exam date.")
        return

    if st.button("Generate CSP Timetable", type="primary", use_container_width=True):
        all_tasks = []
        for co, info in SYLLABUS.items():
            comp = completed.get(co, [])
            qs = quiz_scores.get(co, 50)
            is_weak = qs < 60
            high_diff = info["difficulty"] in ["Hard", "Very Hard"]
            est = {"Medium": 1.0, "Hard": 1.5, "Very Hard": 2.0}.get(info["difficulty"], 1.0)

            for topic in info["topics"]:
                if topic not in comp:
                    all_tasks.append(
                        {
                            "co": co, "topic": topic,
                            "high_diff": high_diff, "is_weak": is_weak,
                            "est": est, "difficulty": info["difficulty"],
                        }
                    )

        # Weak topics get a second appearance (C3)
        extra = [
            {**t, "topic": f"[WEAK REVISION] {t['topic']}", "is_weak": True}
            for t in all_tasks if t["is_weak"]
        ][:4]
        all_tasks = all_tasks + extra

        timetable = []
        constraint_log = []
        cur_date = date.today()
        day_tasks, hours_used, day_has_hard = [], 0.0, False

        for task in all_tasks:
            if cur_date >= exam_dt - timedelta(days=3):
                break

            # C1: daily hour limit
            if hours_used + task["est"] > user["daily_hours"]:
                if day_tasks:
                    timetable.append({"date": cur_date, "tasks": day_tasks.copy()})
                cur_date += timedelta(days=1)
                day_tasks, hours_used, day_has_hard = [], 0.0, False
                if cur_date >= exam_dt - timedelta(days=3):
                    break

            # C2: no two hard topics same day
            if task["high_diff"] and day_has_hard:
                constraint_log.append(
                    f"C2: '{task['topic']}' moved to next day — another hard topic already on {cur_date.strftime('%d %b')}"
                )
                if day_tasks:
                    timetable.append({"date": cur_date, "tasks": day_tasks.copy()})
                cur_date += timedelta(days=1)
                day_tasks, hours_used, day_has_hard = [], 0.0, False
                if cur_date >= exam_dt - timedelta(days=3):
                    break

            day_tasks.append(task)
            hours_used += task["est"]
            if task["high_diff"]:
                day_has_hard = True

        if day_tasks:
            timetable.append({"date": cur_date, "tasks": day_tasks})

        # C4: revision days (last 3 days)
        rev_topics = ["A* Search", "CSP Modeling", "Bayes Rule", "Minimax Algorithm", "PEAS Framework", "Hybrid Architecture: Rule + Search + Probabilistic"]
        rev_start = exam_dt - timedelta(days=3)
        for i in range(3):
            rd = rev_start + timedelta(days=i)
            rts = rev_topics[i * 2: (i + 1) * 2]
            timetable.append(
                {
                    "date": rd,
                    "tasks": [
                        {"co": "All", "topic": f"[REVISION] {t}", "difficulty": "Review", "is_weak": False, "high_diff": False}
                        for t in rts
                    ],
                }
            )

        st.markdown("---")
        st.subheader("Generated Timetable")
        rows = []
        for entry in timetable:
            for task in entry["tasks"]:
                rows.append(
                    {
                        "Date": entry["date"].strftime("%d %b %Y (%a)"),
                        "CO": task["co"],
                        "Topic": task["topic"],
                        "Difficulty": task["difficulty"],
                        "Weak/Revision": "Yes" if task["is_weak"] else ("Revision" if "REVISION" in task["topic"] else "No"),
                    }
                )

        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No pending topics to schedule.")

        if constraint_log:
            st.markdown("---")
            st.subheader("Constraint Decisions Made")
            for entry in constraint_log:
                st.write(f"- {entry}")

        st.markdown("---")
        st.subheader("Connection to CO3")
        st.write(
            "In this timetable, each **day** is a CSP variable. "
            "The **topics assigned** are the values. "
            "The rules above are the **constraints**. "
            "In a real CSP solver, backtracking would be used if no valid assignment is found. "
            "Here we use a greedy forward approach with simple constraint checks."
        )

def page_revision():
    user = get_user()
    completed = user.get("completed_topics", {})
    quiz_scores = user.get("quiz_scores", {})

    st.title("Revision Plan")

    try:
        exam_dt = datetime.strptime(user["exam_date"], "%Y-%m-%d").date()
        days_left = (exam_dt - date.today()).days
    except Exception:
        days_left = 30

    if days_left <= 3:
        st.warning(f"Exam is in {days_left} days. Focus on revision only.")
    else:
        st.write(f"Exam in **{days_left} days**. Here is what to prioritise for revision.")

    st.subheader("Weak Topics from Quiz")
    found = False
    for co in SYLLABUS:
        s = quiz_scores.get(co, None)
        if s is not None and s < 70:
            comp = completed.get(co, [])
            pending = [t for t in SYLLABUS[co]["topics"] if t not in comp][:3]
            if pending:
                st.markdown(f"**{co}** (Score: {s:.0f}%) — review:")
                for t in pending:
                    st.write(f"  - {t}")
                found = True
    if not found:
        st.write("No obvious weak topics. Take quizzes if you haven't already.")

    st.markdown("---")
    st.subheader("High-Priority Topics — Do Not Skip")

    must_do = [
        ("CO1", "PEAS Framework"),
        ("CO1", "Problem Formulation: State, Action, Transition, Cost"),
        ("CO2", "A* Search"),
        ("CO2", "BFS and DFS"),
        ("CO3", "CSP Modeling"),
        ("CO3", "MRV Heuristic"),
        ("CO4", "Minimax Algorithm"),
        ("CO4", "Alpha-Beta Pruning"),
        ("CO5", "Bayes Rule"),
        ("CO5", "Bayesian Networks: CPT"),
        ("CO6", "Explainable Reasoning Traces"),
        ("CO6", "Hybrid Architecture: Rule + Search + Probabilistic"),
    ]

    c1, c2 = st.columns(2)
    for i, (co, topic) in enumerate(must_do):
        comp = completed.get(co, [])
        # partial match since some topic names may differ slightly
        done = any(topic in t for t in comp)
        color = "green" if done else "orange"
        status = "Done" if done else "Pending"
        with c1 if i % 2 == 0 else c2:
            st.markdown(f"<span style='color:{color}'>● [{co}] {topic} — {status}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Last 3 Days Revision Schedule")

    last3 = {
        "Day 1 (3 days before)": [
            "A* Search — trace f(n)=g(n)+h(n) on paper",
            "Bayes Rule — practice with numbers",
            "Bayesian Networks: CPT — read a CPT table",
        ],
        "Day 2 (2 days before)": [
            "CSP Modeling — write variables/domains/constraints",
            "Minimax Algorithm — draw a game tree",
            "Alpha-Beta Pruning — trace α and β updates",
        ],
        "Day 3 (1 day before)": [
            "PEAS Framework — write for 3 different agents",
            "Explainable Reasoning Traces — give an example",
            "Quick scan of all formulas and key definitions",
        ],
    }

    for day, topics in last3.items():
        with st.expander(day):
            for t in topics:
                st.write(f"- {t}")

    st.markdown("---")
    st.subheader("Pending Topics by CO")
    for co, info in SYLLABUS.items():
        comp = completed.get(co, [])
        pending = [t for t in info["topics"] if t not in comp]
        if pending:
            with st.expander(f"{co} — {len(pending)} pending"):
                for t in pending:
                    st.write(f"- {t}")

def page_admin():
    st.title("Admin Panel")
    st.write("Logged in as admin. Note: changes are session-only and reset when the app restarts.")

    tab1, tab2, tab3, tab4 = st.tabs(["Students", "Syllabus", "Quiz Questions", "Reports"])

    with tab1:
        st.subheader("All Registered Students")
        rows = []
        for email, s in st.session_state.users.items():
            qs = s.get("quiz_scores", {})
            avg = sum(qs.values()) / len(qs) if qs else 0
            comp = s.get("completed_topics", {})
            done = sum(len(v) for v in comp.values())
            total = sum(len(SYLLABUS[co]["topics"]) for co in SYLLABUS)
            rows.append(
                {
                    "Name": s["name"],
                    "Roll": s["roll"],
                    "Email": email,
                    "Semester": s["semester"],
                    "Level": s["level"],
                    "Topics Done": f"{done}/{total}",
                    "Quiz Avg": f"{avg:.0f}%",
                    "Exam Date": s["exam_date"],
                }
            )
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.write("No students registered.")

        st.subheader("Reset Student Progress")
        emails = list(st.session_state.users.keys())
        if emails:
            sel_email = st.selectbox("Select student:", emails)
            if st.button("Reset Progress", type="primary"):
                st.session_state.users[sel_email]["completed_topics"] = {}
                st.session_state.users[sel_email]["quiz_scores"] = {}
                st.session_state.users[sel_email]["study_plan"] = []
                st.success(f"Progress reset for {sel_email}.")

    with tab2:
        st.subheader("Syllabus Overview")
        for co, info in SYLLABUS.items():
            with st.expander(f"{co} — {info['title']}"):
                for t in info["topics"]:
                    st.write(f"- {t}")

        st.subheader("Add Topic (session-only)")
        new_co = st.selectbox("CO:", list(SYLLABUS.keys()), key="admin_co")
        new_topic = st.text_input("Topic Name:")
        if st.button("Add Topic"):
            if new_topic.strip():
                SYLLABUS[new_co]["topics"].append(new_topic.strip())
                st.success(f"Added '{new_topic}' to {new_co}")
            else:
                st.warning("Topic name cannot be empty.")

    with tab3:
        st.subheader("View Quiz Questions")
        view_co = st.selectbox("CO:", list(QUIZ_QUESTIONS.keys()), key="admin_view_co")
        for i, q in enumerate(QUIZ_QUESTIONS.get(view_co, [])):
            st.write(f"**Q{i+1}:** {q['q']}")
            st.write(f"Correct: {q['options'][q['answer']]}")
            st.write("---")

        st.subheader("Add Quiz Question (session-only)")
        add_co = st.selectbox("CO:", list(QUIZ_QUESTIONS.keys()), key="admin_add_co")
        q_text = st.text_input("Question text:")
        opt_a = st.text_input("Option A:")
        opt_b = st.text_input("Option B:")
        opt_c = st.text_input("Option C:")
        opt_d = st.text_input("Option D:")
        correct_opt = st.selectbox("Correct Option:", ["A", "B", "C", "D"])
        topic_ref = st.text_input("Topic (for reference):")

        if st.button("Add Question"):
            if q_text and opt_a and opt_b and opt_c and opt_d:
                idx = ["A", "B", "C", "D"].index(correct_opt)
                QUIZ_QUESTIONS[add_co].append(
                    {
                        "q": q_text,
                        "options": [opt_a, opt_b, opt_c, opt_d],
                        "answer": idx,
                        "topic": topic_ref,
                    }
                )
                st.success("Question added.")
            else:
                st.warning("Please fill in all fields.")

    with tab4:
        st.subheader("Weak Topic Report")
        report = {}
        for email, s in st.session_state.users.items():
            for co, score in s.get("quiz_scores", {}).items():
                if score < 60:
                    if co not in report:
                        report[co] = []
                    report[co].append({"Student": s["name"], "Email": email, "Score": f"{score:.0f}%"})

        if report:
            for co, entries in report.items():
                st.write(f"**{co}** — students with score below 60%:")
                st.dataframe(pd.DataFrame(entries), use_container_width=True, hide_index=True)
        else:
            st.write("No students have quiz scores below 60% yet, or no quizzes have been taken.")

def page_limitations():
    st.title("Project Limitations and Notes")
    st.write(
        "This section documents what this project does and does not do. "
        "Knowing the limitations of your own work is an important part of honest engineering."
    )

    st.subheader("Current Limitations")
    items = [
        "The recommendation system uses a rule-based priority formula, not real machine learning or a trained model.",
        "All data (user accounts, progress, quiz scores) is stored in session_state and resets when the app is restarted. "
        "To make it permanent, JSON file storage would need to be added.",
        "The exam readiness score is a simple weighted estimate, not a statistically validated predictor.",
        "The algorithm visualizer only works on a small fixed graph. It does not support user-defined graphs.",
        "The CSP timetable uses a greedy forward approach, not a complete backtracking solver.",
        "Passwords are stored in plain text in session_state. A real system would use hashing.",
        "Quiz questions are hand-written and limited in number. A larger randomised bank would be better.",
        "The study plan does not auto-update when topics are completed — it must be regenerated manually.",
    ]
    for item in items:
        st.write(f"- {item}")

    st.subheader("Possible Future Enhancements")
    enhancements = [
        "Save user data to a JSON file so progress is not lost on restart.",
        "Use a real probabilistic model (e.g., logistic regression) for better readiness prediction.",
        "Add more quiz questions with a question bank stored in a separate file.",
        "Allow users to add their own graphs in the algorithm visualizer.",
        "Implement proper backtracking CSP with arc consistency for the timetable.",
        "Add password hashing using hashlib or bcrypt.",
        "Send email reminders for exam dates using smtplib.",
        "Add a group study mode for multiple students to collaborate.",
    ]
    for e in enhancements:
        st.write(f"- {e}")

    st.subheader("CO-wise Concept Mapping")
    st.markdown("""
| CFAI CO | Concept | Used in this project |
|---|---|---|
| CO1 | Agent model, PEAS, problem formulation, Python data structures | Recommendation system acts as an agent; priority queue used internally |
| CO2 | Search algorithms: BFS, DFS, UCS, Greedy, A* | Algorithm Visualizer (direct implementation) |
| CO3 | CSP modeling, backtracking, constraint propagation | CSP Timetable Generator |
| CO4 | Utility functions, decision-making under limits | Priority Score formula drives all recommendations |
| CO5 | Probability, Bayes, uncertainty | Exam readiness score is a weighted probabilistic estimate |
| CO6 | Hybrid AI, explainability, ethics, limitations | Recommendations give reasons; this limitations page itself |
    """)

    st.subheader("Viva Explanation (Simple Version)")
    st.write(
        "This project is a study planning tool for CFAI students. "
        "It has six main ideas from the course built into it:"
    )
    st.write(
        "1. The recommendation system works like an agent (CO1) — it looks at what topics are pending, "
        "how difficult they are, and how well the student did in quizzes, then suggests what to study next.\n\n"
        "2. The algorithm visualizer (CO2) directly runs BFS, DFS, UCS, Greedy, and A* on a 7-node graph and shows which nodes were visited.\n\n"
        "3. The CSP timetable (CO3) assigns topics to days while checking constraints like 'no two hard topics on the same day'.\n\n"
        "4. The priority score formula (CO4) is inspired by utility functions — it scores each pending topic and picks the best one.\n\n"
        "5. The exam readiness score (CO5) is a simple probability-style estimate based on three weighted factors — completion, quiz average, and time left.\n\n"
        "6. The recommendations page gives plain-language reasons for every suggestion, which is a basic form of explainable AI (CO6). "
        "The limitations page also covers the ethics and honest assessment of what the project can and cannot do."
    )

