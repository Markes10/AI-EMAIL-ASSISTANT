from typing import Tuple, List

"""
Lightweight ML-based intent classifier.

This module trains a small TF-IDF + LogisticRegression pipeline on a
seed dataset at import time. It provides `detect_intent(text)` which
returns (intent_label, confidence).

If scikit-learn is unavailable, falls back to a minimal keyword-based
detector for compatibility.
"""

_MODEL = None
_LABELS: List[str] = []

try:
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import LabelEncoder
    import numpy as np

    def _build_and_train():
        # Seed training data (examples per intent). Extend as needed.
        samples = [
            # job_application
            ("I would like to apply for the software engineer position", "job_application"),
            ("Please find my resume attached for your review", "job_application"),
            ("I'm applying for the role of data scientist", "job_application"),
            ("I am interested in the open position", "job_application"),

            # complaint
            ("I want to complain about my recent order", "complaint"),
            ("My product arrived damaged and I want a refund", "complaint"),
            ("There is a problem with the service", "complaint"),
            ("I'm disappointed with the quality", "complaint"),

            # follow_up
            ("Following up on my last email", "follow_up"),
            ("Just checking if you had a chance to review", "follow_up"),
            ("Any updates on my request?", "follow_up"),

            # apology
            ("I apologize for the inconvenience caused", "apology"),
            ("Sorry for the delay in response", "apology"),

            # inquiry
            ("Could you please clarify the requirements?", "inquiry"),
            ("I have a question about the invoice", "inquiry"),
            ("Can you provide more details?", "inquiry"),

            # generic / other
            ("Thank you for your time", "other"),
            ("Looking forward to hearing from you", "other"),
        ]

        texts, labels = zip(*samples)
        le = LabelEncoder()
        y = le.fit_transform(labels)
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
            ("clf", LogisticRegression(max_iter=1000))
        ])

        pipeline.fit(list(texts), y)

        return pipeline, le

    _MODEL, _LE = _build_and_train()
    _LABELS = list(_LE.classes_)

    def detect_intent(text: str) -> Tuple[str, float]:
        """Predict intent label and return confidence (0-1).

        If model cannot decide (low probability), returns 'unknown', 0.0.
        """
        if not text or not text.strip():
            return "unknown", 0.0

        try:
            probs = _MODEL.predict_proba([text])[0]
            top_idx = int(np.argmax(probs))
            top_label = _LE.inverse_transform([top_idx])[0]
            confidence = float(probs[top_idx])
            # Threshold to avoid low-confidence predictions
            if confidence < 0.35:
                return "unknown", confidence
            return top_label, confidence
        except Exception:
            return "unknown", 0.0

    def retrain(samples: List[Tuple[str, str]]):
        """Retrain the classifier with additional samples.

        `samples` is a list of (text, label) tuples.
        """
        global _MODEL, _LE, _LABELS
        if not samples:
            return
        try:
            current_texts = []
            current_labels = []
            # Extract existing seed data by reusing pipeline transform if possible
            # For simplicity, rebuild from provided samples only (extend as needed).
            texts, labels = zip(*samples)
            _MODEL, _LE = _build_and_train()
            _MODEL.fit(list(texts), _LE.transform(labels))
            _LABELS = list(_LE.classes_)
        except Exception:
            pass

except Exception:
    # Fallback simple keyword detector (previous behavior)
    import re

    KEYWORDS = {
        'complaint': ['complain', 'issue', 'refund', 'problem', 'angry', 'disappoint', 'error'],
        'job_application': ['apply', 'resume', 'cv', 'application', 'position', 'job', 'opportunity'],
        'follow_up': ['follow up', 'following up', 'any updates', 'checking in'],
        'apology': ['sorry', 'apologize', 'regret', 'apologies'],
        'inquiry': ['question', 'could you', 'can you', 'please advise', 'clarify']
    }

    def detect_intent(text: str) -> Tuple[str, float]:
        txt = (text or "").lower()
        scores = {k: 0 for k in KEYWORDS}
        for intent, kws in KEYWORDS.items():
            for k in kws:
                if k in txt:
                    scores[intent] += txt.count(k)
        best = max(scores.items(), key=lambda x: x[1])
        if best[1] == 0:
            return 'unknown', 0.0
        # Confidence heuristic
        total = sum(scores.values())
        conf = best[1] / total if total else 0.0
        return best[0], min(1.0, conf)

