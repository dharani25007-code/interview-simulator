"""
AI Engine — handles all Groq API calls for question generation,
answer evaluation, follow-up questions, and learning tips.

Groq uses an OpenAI-compatible SDK. Model used: llama-3.3-70b-versatile
which is fast, free-tier friendly, and excellent for structured JSON output.
"""

import os
import json
from groq import Groq

# ── Client setup ──────────────────────────────────────────────────────────────
client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

# Best free model on Groq for instruction-following + JSON output.
# Alternatives you can swap in:
#   "llama-3.1-8b-instant"   — faster, slightly weaker
#   "mixtral-8x7b-32768"     — good for longer context
#   "gemma2-9b-it"           — Google's Gemma 2
GROQ_MODEL = "llama-3.3-70b-versatile"


def _call_groq(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """Helper: call Groq chat completion and return the assistant text."""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


def _parse_json(text: str) -> dict:
    """Strip markdown fences and parse JSON safely."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:] if lines[-1].strip() == "```" else lines[1:])
        text = text.rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
        return {"raw": text}


class AIEngine:
    """Encapsulates all AI-powered interview logic using Groq."""

    def generate_first_question(self, role: str, level: str, category: str) -> dict:
        system = (
            "You are an expert technical interviewer. "
            "You MUST respond with ONLY a valid JSON object — no explanation, "
            "no markdown, no extra text before or after the JSON."
        )
        user = f"""Generate the first interview question for:
- Role: {role}
- Level: {level} (junior / mid / senior)
- Category: {category} (technical / hr / mixed)

Start with a warm-up question appropriate for this role and level.

Respond with ONLY this JSON (no other text):
{{
  "text": "<question text here>",
  "type": "technical",
  "difficulty": 3,
  "keywords": ["keyword1", "keyword2"]
}}"""
        result = _parse_json(_call_groq(system, user))
        return {
            "text":       result.get("text", "Tell me about yourself and your background."),
            "type":       result.get("type", "hr"),
            "difficulty": int(result.get("difficulty", 3)),
            "keywords":   result.get("keywords", [])
        }

    def generate_next_question(self, role, level, category, difficulty, previous_questions, last_score) -> dict:
        system = (
            "You are an expert technical interviewer who adapts difficulty "
            "based on candidate performance. "
            "Respond with ONLY a valid JSON object — no extra text."
        )
        prev_list = "\n".join(f"- {q}" for q in previous_questions[-3:])
        user = f"""Generate the next interview question.

Context:
- Role: {role}, Level: {level}, Category: {category}
- Target difficulty: {difficulty}/10
- Last answer score: {last_score}/100
- Recent questions asked (do NOT repeat these):
{prev_list}

Rules:
- Do NOT repeat or rephrase any previous question
- Match the target difficulty: {difficulty}/10
- If last score < 40 ask something easier; if > 75 go harder
- For "mixed" category, alternate between technical and HR

Respond with ONLY this JSON:
{{
  "text": "<question text>",
  "type": "technical",
  "difficulty": {difficulty},
  "keywords": ["keyword1", "keyword2"]
}}"""
        result = _parse_json(_call_groq(system, user))
        return {
            "text":       result.get("text", "Describe a challenging project you have worked on."),
            "type":       result.get("type", "technical"),
            "difficulty": int(result.get("difficulty", difficulty)),
            "keywords":   result.get("keywords", [])
        }

    def generate_followup(self, original_question, answer, interview_role) -> dict:
        system = (
            "You are an interviewer probing for deeper understanding. "
            "Respond with ONLY a valid JSON object."
        )
        user = f"""The candidate was asked: "{original_question}"
Their answer: "{answer[:500]}"
Role: {interview_role}

Their answer was vague or too short. Generate ONE follow-up question
that probes deeper into what they said or failed to mention.

Respond with ONLY this JSON:
{{
  "text": "<follow-up question>",
  "keywords": ["keyword1", "keyword2"]
}}"""
        result = _parse_json(_call_groq(system, user))
        return {
            "text":     result.get("text", "Can you elaborate with a specific example?"),
            "keywords": result.get("keywords", [])
        }

    def evaluate_answer(self, question, answer, expected_keywords, question_type, difficulty) -> dict:
        system = (
            "You are an expert interview evaluator. Be constructive but honest. "
            "Respond with ONLY a valid JSON object — no extra text."
        )
        kw_str = ", ".join(expected_keywords) if expected_keywords else "none specified"
        user = f"""Evaluate this interview answer.

Question: "{question}"
Question type: {question_type}
Difficulty: {difficulty}/10
Expected keywords/concepts: {kw_str}
Candidate's answer: "{answer[:1000]}"

Scoring rubric (total = 100 pts):
- Correctness (40 pts): factually accurate and relevant?
- Keyword coverage (30 pts): covers key concepts?
- Clarity (30 pts): well-structured and easy to follow?

Respond with ONLY this JSON (extremely important: teacher_explanation should be an expert technical breakdown):
{{
  "score": <integer 0-100>,
  "feedback": "<2-3 sentences of constructive feedback>",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "improvements": "<short actionable improvement>",
  "ideal_answer": "<a comprehensive, expert-level model answer for this specific role/level>",
  "teacher_explanation": "<a detailed technical breakdown of the concept, explaining why the user is correct/incorrect, common pitfalls, and advanced nuances like a senior tutor would>",
  "structured_resources": [
    {{"title": "Resource title", "description": "Short desc", "url": "verified_url_or_search_query"}}
  ],
  "needs_followup": <true if answer is under 40 words or very vague, else false>,
  "correctness_score": <integer 0-40>,
  "keyword_score": <integer 0-30>,
  "clarity_score": <integer 0-30>
}}

URL RULES for "structured_resources":
1. NEVER hallucinate or guess a direct URL. Broken links are worse than no links.
2. ONLY use high-authority domains: developer.mozilla.org, geeksforgeeks.org, leetcode.com, stackoverflow.com, youtube.com, wikipedia.org.
3. If not 100% certain of a direct link, use a Google Search or YouTube search query:
   - https://www.google.com/search?q=<topic+name+tutorial>
   - https://www.youtube.com/results?search_query=<topic+name+explained>
4. Ensure the URL is properly formatted and safe."""
        result = _parse_json(_call_groq(system, user, max_tokens=1500)) # Increased tokens for detailed teacher explanation
        score = max(0, min(100, int(result.get("score", 50))))
        return {
            "score":               score,
            "feedback":            result.get("feedback", "Good attempt. Keep practising."),
            "strengths":           result.get("strengths", []),
            "weaknesses":          result.get("weaknesses", []),
            "improvements":        result.get("improvements", ""),
            "ideal_answer":        result.get("ideal_answer", ""),
            "teacher_explanation": result.get("teacher_explanation", ""),
            "structured_resources": result.get("structured_resources", []),
            "needs_followup":      result.get("needs_followup", len(answer.split()) < 30),
            "correctness_score":   result.get("correctness_score", 0),
            "keyword_score":       result.get("keyword_score", 0),
            "clarity_score":       result.get("clarity_score", 0)
        }

    def generate_learning_tips(self, role, weaknesses, avg_score) -> list:
        system = (
            "You are an expert career coach. "
            "Respond with ONLY a valid JSON array — no extra text."
        )
        weak_str = ", ".join(weaknesses) if weaknesses else "general interview skills"
        user = f"""A candidate for {role} completed an interview.
Average score: {avg_score}/100
Key weaknesses: {weak_str}

Generate exactly 4 specific, actionable learning tips.

Respond with ONLY this JSON array:
[
  {{
    "title": "<short tip title>",
    "description": "<1-2 sentence actionable advice>",
    "resource": "<specific book, course, or practice method>"
  }}
]"""
        raw = _call_groq(system, user, max_tokens=700)
        try:
            parsed = _parse_json(raw)
            if isinstance(parsed, list):
                return parsed[:4]
            for key in ("tips", "learning_tips", "results"):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key][:4]
        except Exception:
            pass
        return [
            {"title": "Daily coding practice", "description": "Solve 2 LeetCode problems daily focusing on your weak areas.", "resource": "LeetCode Top 150"},
            {"title": "System design study", "description": "Learn scalable architecture patterns used in real interviews.", "resource": "\"Designing Data-Intensive Applications\" by Kleppmann"},
            {"title": "Use the STAR method", "description": "Structure all behavioural answers as Situation, Task, Action, Result.", "resource": "\"Cracking the Coding Interview\" by McDowell"},
            {"title": "Weekly mock interviews", "description": "One timed mock per week builds real interview confidence.", "resource": "Pramp.com or interviewing.io"}
        ]