# modules/utils.py
# Utility logic for readiness calculation and study-plan generation.

from datetime import datetime, date, timedelta
from modules.data import SYLLABUS

def calculate_readiness(user):
    """
    Exam readiness estimate:
      40% from syllabus completion
      40% from quiz average
      20% from time remaining
    """
    completed = user.get("completed_topics", {})
    quiz_scores = user.get("quiz_scores", {})

    total = sum(len(SYLLABUS[co]["topics"]) for co in SYLLABUS)
    done = sum(len(completed.get(co, [])) for co in SYLLABUS)
    comp_pct = (done / total * 100) if total else 0

    quiz_avg = sum(quiz_scores.values()) / len(quiz_scores) if quiz_scores else 0

    try:
        exam_dt = datetime.strptime(user["exam_date"], "%Y-%m-%d").date()
    except Exception:
        exam_dt = date.today() + timedelta(days=30)

    days_left = max(0, (exam_dt - date.today()).days)

    if days_left > 20:
        time_score = 100
    elif days_left > 10:
        time_score = 70
    elif days_left > 5:
        time_score = 40
    else:
        time_score = 10

    readiness = comp_pct * 0.4 + quiz_avg * 0.4 + time_score * 0.2

    return {
        "readiness": round(readiness, 1),
        "comp_pct": round(comp_pct, 1),
        "quiz_avg": round(quiz_avg, 1),
        "time_score": time_score,
        "days_left": days_left,
        "done": done,
        "total": total,
    }

def generate_study_plan(user):
    """
    Simple greedy study plan generator.
    Priority Score = difficulty + importance + weakness_penalty
    Topics are assigned to days respecting the daily hour limit.
    """
    completed = user.get("completed_topics", {})
    quiz_scores = user.get("quiz_scores", {})
    daily_hours = user.get("daily_hours", 3)

    try:
        exam_dt = datetime.strptime(user["exam_date"], "%Y-%m-%d").date()
    except Exception:
        exam_dt = date.today() + timedelta(days=30)

    today = date.today()
    if exam_dt <= today:
        return []

    # Build pending topic list with priority scores
    tasks = []
    for co, info in SYLLABUS.items():
        comp = completed.get(co, [])
        qs = quiz_scores.get(co, 50)
        weakness = max(0, (100 - qs) / 100)

        diff_val = {"Medium": 2, "Hard": 3, "Very Hard": 4}.get(info["difficulty"], 2)
        imp_val = {"High": 3, "Very High": 4}.get(info["importance"], 3)

        for topic in info["topics"]:
            if topic not in comp:
                score = diff_val + imp_val + weakness * 3
                tasks.append(
                    {
                        "CO": co,
                        "Topic": topic,
                        "Priority Score": round(score, 1),
                        "Est. Time (hrs)": round(diff_val * 0.5, 1),
                        "Difficulty": info["difficulty"],
                    }
                )

    tasks.sort(key=lambda x: -x["Priority Score"])

    plan = []
    cur_date = today
    hours_used = 0.0

    for task in tasks:
        if cur_date >= exam_dt - timedelta(days=3):
            break
        if hours_used + task["Est. Time (hrs)"] > daily_hours:
            cur_date += timedelta(days=1)
            hours_used = 0.0
            if cur_date >= exam_dt - timedelta(days=3):
                break
        plan.append(
            {
                "Date": cur_date.strftime("%d %b %Y"),
                "CO": task["CO"],
                "Topic": task["Topic"],
                "Est. Time (hrs)": task["Est. Time (hrs)"],
                "Priority Score": task["Priority Score"],
                "Difficulty": task["Difficulty"],
                "Status": "Pending",
            }
        )
        hours_used += task["Est. Time (hrs)"]

    # Add a short revision block in the last 3 days
    rev_topics = [
        "A* Search",
        "CSP Modeling",
        "Bayes Rule",
        "Minimax Algorithm",
        "PEAS Framework",
        "Hybrid Architecture: Rule + Search + Probabilistic",
    ]
    rev_start = exam_dt - timedelta(days=3)
    for i, rt in enumerate(rev_topics):
        rd = rev_start + timedelta(days=i // 2)
        if rd < exam_dt:
            plan.append(
                {
                    "Date": rd.strftime("%d %b %Y"),
                    "CO": "All",
                    "Topic": f"[REVISION] {rt}",
                    "Est. Time (hrs)": 1.0,
                    "Priority Score": 10.0,
                    "Difficulty": "Review",
                    "Status": "Pending",
                }
            )

    return plan

