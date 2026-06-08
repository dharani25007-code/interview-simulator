"""
AI-Powered Interview Simulator - Flask Backend
Main application entry point with all API routes.
"""

# Load .env variables before anything else
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from datetime import timedelta
import os
import json
from database import db, User, Interview, Question, Answer
from ai_engine import AIEngine
from analytics import AnalyticsEngine

# ─── App Setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///interview_simulator.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-in-prod")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

db.init_app(app)
jwt = JWTManager(app)
ai = AIEngine()
analytics = AnalyticsEngine()

# Create tables on startup
with app.app_context():
    db.create_all()


# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.route("/api/auth/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json()
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validation
    if not all([name, email, password]):
        return jsonify({"error": "All fields are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "token": token,
        "user": user.to_dict()
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT."""
    data     = request.get_json()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "token": token,
        "user": user.to_dict()
    })


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def get_me():
    """Return the current authenticated user's profile."""
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict())


# ─── Dashboard Routes ─────────────────────────────────────────────────────────

@app.route("/api/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard():
    """Return dashboard stats, history, and readiness index."""
    user_id = get_jwt_identity()
    interviews = Interview.query.filter_by(
        user_id=user_id, status="completed"
    ).order_by(Interview.created_at.desc()).all()

    stats = analytics.compute_stats(interviews)
    readiness = analytics.compute_readiness_index(interviews)
    history = [iv.to_summary() for iv in interviews[:10]]

    return jsonify({
        "stats": stats,
        "readiness": readiness,
        "history": history
    })


# ─── Interview Routes ─────────────────────────────────────────────────────────

@app.route("/api/interviews/start", methods=["POST"])
@jwt_required()
def start_interview():
    """Create a new interview session and return the first question."""
    user_id = get_jwt_identity()
    data = request.get_json()
    role     = data.get("role", "Software Engineer")
    level    = data.get("level", "mid")      # junior / mid / senior
    category = data.get("category", "mixed") # technical / hr / mixed

    interview = Interview(
        user_id=user_id,
        role=role,
        level=level,
        category=category,
        status="active",
        current_difficulty=5  # 1-10 scale, starts at 5
    )
    db.session.add(interview)
    db.session.commit()

    # Generate opening question via AI
    first_q = ai.generate_first_question(role, level, category)
    question = Question(
        interview_id=interview.id,
        text=first_q["text"],
        type=first_q["type"],
        difficulty=first_q["difficulty"],
        expected_keywords=",".join(first_q.get("keywords", [])),
        order=1
    )
    db.session.add(question)
    db.session.commit()

    return jsonify({
        "interview_id": interview.id,
        "question": question.to_dict()
    }), 201


@app.route("/api/interviews/<int:interview_id>/answer", methods=["POST"])
@jwt_required()
def submit_answer(interview_id):
    """
    Submit an answer, evaluate it with AI, adapt difficulty,
    and return the next question (or end the interview).
    """
    user_id   = get_jwt_identity()
    interview = Interview.query.filter_by(
        id=interview_id, user_id=user_id
    ).first_or_404()

    if interview.status != "active":
        return jsonify({"error": "Interview is not active"}), 400

    data        = request.get_json()
    question_id = data.get("question_id")
    answer_text = data.get("answer", "").strip()
    time_taken  = data.get("time_taken", 0)

    question = Question.query.filter_by(
        id=question_id, interview_id=interview_id
    ).first_or_404()

    if not answer_text:
        return jsonify({"error": "Answer cannot be empty"}), 400

    # ── AI Evaluation ──────────────────────────────────────────────────────
    evaluation = ai.evaluate_answer(
        question=question.text,
        answer=answer_text,
        expected_keywords=question.expected_keywords.split(",") if question.expected_keywords else [],
        question_type=question.type,
        difficulty=question.difficulty
    )

    # Save answer record
    answer = Answer(
        question_id=question.id,
        interview_id=interview.id,
        text=answer_text,
        score=evaluation["score"],
        feedback=evaluation["feedback"],
        strengths=",".join(evaluation.get("strengths", [])),
        weaknesses=",".join(evaluation.get("weaknesses", [])),
        improvements=evaluation.get("improvements", ""),
        ideal_answer=evaluation.get("ideal_answer", ""),
        teacher_explanation=evaluation.get("teacher_explanation", ""),
        detailed_resources=json.dumps(evaluation.get("structured_resources", [])),
        resources=",".join([r.get("url", "") for r in evaluation.get("structured_resources", [])]),
        time_taken=time_taken
    )
    db.session.add(answer)

    # ── Adaptive Difficulty ─────────────────────────────────────────────────
    score = evaluation["score"]
    if score >= 75:
        interview.current_difficulty = min(10, interview.current_difficulty + 1)
    elif score < 40:
        interview.current_difficulty = max(1, interview.current_difficulty - 1)

    question_count = Question.query.filter_by(interview_id=interview_id).count()
    db.session.commit()

    # ── Decide: follow-up, next question, or end ────────────────────────────
    MAX_QUESTIONS = 8

    # Ask a follow-up if the answer was very brief or AI flagged it
    if evaluation.get("needs_followup") and question_count < MAX_QUESTIONS:
        followup = ai.generate_followup(
            original_question=question.text,
            answer=answer_text,
            interview_role=interview.role
        )
        next_q = Question(
            interview_id=interview.id,
            text=followup["text"],
            type="followup",
            difficulty=question.difficulty,
            expected_keywords=",".join(followup.get("keywords", [])),
            order=question_count + 1
        )
        db.session.add(next_q)
        db.session.commit()
        return jsonify({
            "evaluation": evaluation,
            "next_question": next_q.to_dict(),
            "is_followup": True,
            "progress": {"current": question_count + 1, "total": MAX_QUESTIONS}
        })

    # End the interview when max questions reached
    if question_count >= MAX_QUESTIONS:
        interview.status = "completed"
        db.session.commit()
        report = _generate_final_report(interview)
        return jsonify({
            "evaluation": evaluation,
            "interview_complete": True,
            "report": report
        })

    # Generate the next adaptive question
    previous_answers = Answer.query.filter_by(interview_id=interview_id).all()
    next_question_data = ai.generate_next_question(
        role=interview.role,
        level=interview.level,
        category=interview.category,
        difficulty=interview.current_difficulty,
        previous_questions=[q.text for q in interview.questions],
        last_score=score
    )
    next_q = Question(
        interview_id=interview.id,
        text=next_question_data["text"],
        type=next_question_data["type"],
        difficulty=next_question_data["difficulty"],
        expected_keywords=",".join(next_question_data.get("keywords", [])),
        order=question_count + 1
    )
    db.session.add(next_q)
    db.session.commit()

    return jsonify({
        "evaluation": evaluation,
        "next_question": next_q.to_dict(),
        "is_followup": False,
        "progress": {"current": question_count + 1, "total": MAX_QUESTIONS}
    })


@app.route("/api/interviews/<int:interview_id>/end", methods=["POST"])
@jwt_required()
def end_interview(interview_id):
    """Manually end an interview early and generate a partial report."""
    user_id   = get_jwt_identity()
    interview = Interview.query.filter_by(
        id=interview_id, user_id=user_id
    ).first_or_404()

    interview.status = "completed"
    db.session.commit()

    report = _generate_final_report(interview)
    return jsonify({"report": report})


@app.route("/api/interviews/<int:interview_id>/report", methods=["GET"])
@jwt_required()
def get_report(interview_id):
    """Fetch the full report for a completed interview."""
    user_id   = get_jwt_identity()
    interview = Interview.query.filter_by(
        id=interview_id, user_id=user_id
    ).first_or_404()

    report = _generate_final_report(interview)
    return jsonify({"report": report})


# ─── Helper: Final Report ─────────────────────────────────────────────────────

def _generate_final_report(interview):
    """Compile scores, feedback, and AI summary for a completed interview."""
    answers = Answer.query.filter_by(interview_id=interview.id).all()
    if not answers:
        return {"error": "No answers found"}

    scores    = [a.score for a in answers]
    avg_score = round(sum(scores) / len(scores))

    all_strengths  = []
    all_weaknesses = []
    for a in answers:
        if a.strengths:
            all_strengths.extend(a.strengths.split(","))
        if a.weaknesses:
            all_weaknesses.extend(a.weaknesses.split(","))

    # Deduplicate and trim
    strengths  = list(set(s.strip() for s in all_strengths if s.strip()))[:5]
    weaknesses = list(set(w.strip() for w in all_weaknesses if w.strip()))[:5]

    # Generate AI learning tips
    tips = ai.generate_learning_tips(
        role=interview.role,
        weaknesses=weaknesses,
        avg_score=avg_score
    )

    qa_pairs = []
    for q in interview.questions:
        ans = next((a for a in answers if a.question_id == q.id), None)
        qa_pairs.append({
            "question": q.text,
            "answer": ans.text if ans else "Not answered",
            "score": ans.score if ans else 0,
            "feedback": ans.feedback if ans else "",
            "improvements": ans.improvements if ans else "",
            "ideal_answer": ans.ideal_answer if ans else "",
            "teacher_explanation": ans.teacher_explanation if ans else "",
            "detailed_resources": json.loads(ans.detailed_resources) if ans and ans.detailed_resources else [],
            "resources": ans.resources.split(",") if ans and ans.resources else [],
            "type": q.type
        })

    return {
        "interview_id": interview.id,
        "role": interview.role,
        "level": interview.level,
        "avg_score": avg_score,
        "total_questions": len(answers),
        "scores_over_time": scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "learning_tips": tips,
        "qa_pairs": qa_pairs,
        "created_at": interview.created_at.isoformat()
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)
