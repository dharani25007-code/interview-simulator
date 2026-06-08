"""
Analytics Engine — computes the Interview Readiness Index,
performance statistics, and trend analysis.
"""

from statistics import stdev
from database import Answer


class AnalyticsEngine:
    """Computes performance metrics and the Interview Readiness Index."""

    def compute_stats(self, interviews: list) -> dict:
        """Aggregate performance statistics across all completed interviews."""
        if not interviews:
            return {
                "total_interviews": 0,
                "avg_score": 0,
                "best_score": 0,
                "total_questions": 0,
                "improvement_rate": 0
            }

        all_scores = []
        for iv in interviews:
            for ans in iv.answers:
                all_scores.append(ans.score)

        avg = round(sum(all_scores) / len(all_scores)) if all_scores else 0

        # Improvement rate: compare first half vs second half of recent scores
        improvement = 0
        if len(all_scores) >= 4:
            half = len(all_scores) // 2
            first_half_avg = sum(all_scores[:half]) / half
            second_half_avg = sum(all_scores[half:]) / (len(all_scores) - half)
            improvement = round(second_half_avg - first_half_avg, 1)

        return {
            "total_interviews": len(interviews),
            "avg_score": avg,
            "best_score": max(all_scores) if all_scores else 0,
            "total_questions": len(all_scores),
            "improvement_rate": improvement
        }

    def compute_readiness_index(self, interviews: list) -> dict:
        """
        Interview Readiness Index (IRI):
        Combines accuracy (avg score), consistency (low variance),
        and improvement (upward trend).

        Returns: level (Beginner / Intermediate / Ready), score (0-100), breakdown.
        """
        if not interviews:
            return {
                "level": "Beginner",
                "score": 0,
                "breakdown": {
                    "accuracy": 0,
                    "consistency": 0,
                    "improvement": 0
                }
            }

        all_scores = []
        for iv in interviews:
            for ans in iv.answers:
                all_scores.append(ans.score)

        if not all_scores:
            return {"level": "Beginner", "score": 0,
                    "breakdown": {"accuracy": 0, "consistency": 0, "improvement": 0}}

        # ── Accuracy component (40% weight) ─────────────────────────────
        accuracy = sum(all_scores) / len(all_scores)

        # ── Consistency component (30% weight) ──────────────────────────
        # Low variance → high consistency. Normalise standard deviation.
        if len(all_scores) > 1:
            sd = stdev(all_scores)
            # sd of 0 → 100 consistency; sd of 50 → 0 consistency
            consistency = max(0, 100 - (sd * 2))
        else:
            consistency = 50  # neutral when only one data point

        # ── Improvement component (30% weight) ──────────────────────────
        # Compare earliest 30% vs latest 30% of scores
        if len(all_scores) >= 3:
            n3 = max(1, len(all_scores) // 3)
            early = sum(all_scores[:n3]) / n3
            recent = sum(all_scores[-n3:]) / n3
            delta = recent - early  # -100 to +100
            # Map delta to 0-100: delta=+50 → 100, delta=-50 → 0
            improvement = max(0, min(100, 50 + delta))
        else:
            improvement = 50

        # ── Composite IRI ────────────────────────────────────────────────
        iri = round(accuracy * 0.4 + consistency * 0.3 + improvement * 0.3)

        if iri >= 75:
            level = "Ready"
        elif iri >= 45:
            level = "Intermediate"
        else:
            level = "Beginner"

        return {
            "level": level,
            "score": iri,
            "breakdown": {
                "accuracy": round(accuracy),
                "consistency": round(consistency),
                "improvement": round(improvement)
            }
        }
