"""
Storage layer: saves each analysis so results can be looked up later.

Three modes, picked automatically based on environment:
1. USE_FIRESTORE=true, no FIREBASE_CREDENTIALS_PATH -> uses GCP's built-in
   Application Default Credentials. This is the mode used on Cloud Run:
   no key file needed, no secret to manage, the service account attached
   to the Cloud Run service is used automatically.
2. FIREBASE_CREDENTIALS_PATH set -> uses that service account file. Useful
   for local development against a real Firestore project.
3. Neither set -> falls back to a local JSON file that mimics a Firestore
   collection, so the project runs with zero setup. Same read/write
   interface in every mode — nothing else in the app changes.
"""

import json
import os
from pathlib import Path

from app.models import AnalyzeResponse

LOCAL_STORE_PATH = Path(__file__).parent.parent / "local_data" / "analyses.json"


def _use_firestore() -> bool:
    return bool(os.environ.get("USE_FIRESTORE")) or bool(os.environ.get("FIREBASE_CREDENTIALS_PATH"))


def _firestore_client():
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # On Cloud Run / GCP, this picks up Application Default
            # Credentials from the service's attached service account —
            # no key file needed.
            firebase_admin.initialize_app()
    return firestore.client()


def save_analysis(result: AnalyzeResponse) -> None:
    if _use_firestore():
        db = _firestore_client()
        db.collection("analyses").document(result.analysis_id).set(result.model_dump())
        return

    LOCAL_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if LOCAL_STORE_PATH.exists():
        existing = json.loads(LOCAL_STORE_PATH.read_text())
    existing[result.analysis_id] = result.model_dump()
    LOCAL_STORE_PATH.write_text(json.dumps(existing, indent=2))


def get_analysis(analysis_id: str) -> dict | None:
    if _use_firestore():
        db = _firestore_client()
        doc = db.collection("analyses").document(analysis_id).get()
        return doc.to_dict() if doc.exists else None

    if not LOCAL_STORE_PATH.exists():
        return None
    existing = json.loads(LOCAL_STORE_PATH.read_text())
    return existing.get(analysis_id)
