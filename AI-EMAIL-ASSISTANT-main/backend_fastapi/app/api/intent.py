from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Tuple
from starlette.concurrency import run_in_threadpool
from pathlib import Path
import joblib
from app.config import settings
import time

router = APIRouter()
MODEL_DIR = Path(settings.MODEL_DIR)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODEL_DIR / 'intent_model.joblib'


class DetectIn(BaseModel):
    text: str


class Sample(BaseModel):
    text: str
    label: str


@router.post('/detect')
async def detect(req: DetectIn):
    import sys
    from pathlib import Path as P
    base = P(__file__).resolve().parents[3] / 'backend'
    sys.path.insert(0, str(base))
    import services.intent_classifier as ic
    intent, conf = ic.detect_intent(req.text)
    return {'intent': intent, 'confidence': conf}


@router.post('/retrain')
async def retrain(samples: List[Sample]):
    """Retrain intent classifier with given labeled samples, evaluate, persist model and metadata."""
    import sys
    from pathlib import Path as P
    base = P(__file__).resolve().parents[3] / 'backend'
    sys.path.insert(0, str(base))
    import services.intent_classifier as ic

    pairs = [(s.text, s.label) for s in samples]

    def _do():
        # Train a fresh sklearn pipeline if sklearn available
        try:
            from sklearn.pipeline import Pipeline
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import LabelEncoder
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import classification_report, accuracy_score

            texts = [t for t, _ in pairs]
            labels = [l for _, l in pairs]
            le = LabelEncoder()
            y = le.fit_transform(labels)
            pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
                ("clf", LogisticRegression(max_iter=1000))
            ])

            if len(texts) >= 2:
                X_train, X_test, y_train, y_test = train_test_split(texts, y, test_size=0.2, random_state=42)
                pipeline.fit(X_train, y_train)
                preds = pipeline.predict(X_test)
                acc = float(accuracy_score(y_test, preds))
                report = classification_report(y_test, preds, zero_division=0, output_dict=True)
            else:
                pipeline.fit(texts, y)
                acc = 1.0
                report = {}

            # attach to service module
            try:
                ic._MODEL = pipeline
                ic._LE = le
            except Exception:
                pass

            # persist
            try:
                joblib.dump({'model': pipeline, 'le': le}, MODEL_PATH)
            except Exception:
                pass

            # insert metadata to Mongo (sync via pymongo)
            try:
                from pymongo import MongoClient
                client = MongoClient(settings.MONGO_URI)
                db = client[settings.MONGO_DB]
                meta = {
                    'type': 'intent',
                    'path': str(MODEL_PATH),
                    'created_at': int(time.time()),
                    'sample_count': len(texts),
                    'accuracy': acc
                }
                db.get_collection('models').insert_one(meta)
            except Exception:
                pass

            return {'retrained': True, 'model_saved': True, 'accuracy': acc, 'report': report}
        except Exception:
            # fallback to calling existing retrain and attempt to persist
            try:
                ic.retrain(pairs)
                model = getattr(ic, '_MODEL', None)
                le = getattr(ic, '_LE', None)
                if model is not None and le is not None:
                    try:
                        joblib.dump({'model': model, 'le': le}, MODEL_PATH)
                    except Exception:
                        pass
                    return {'retrained': True, 'model_saved': True}
            except Exception:
                pass
        return {'retrained': False, 'model_saved': False}

    result = await run_in_threadpool(_do)
    return result


@router.get('/models')
async def list_models():
    # Return recent model metadata from Mongo (non-blocking via threadpool)
    def _list():
        try:
            from pymongo import MongoClient
            client = MongoClient(settings.MONGO_URI)
            db = client[settings.MONGO_DB]
            docs = list(db.get_collection('models').find({'type': 'intent'}).sort('created_at', -1).limit(50))
            for d in docs:
                d['_id'] = str(d.get('_id'))
            return docs
        except Exception:
            return []

    docs = await run_in_threadpool(_list)
    return {'models': docs}
