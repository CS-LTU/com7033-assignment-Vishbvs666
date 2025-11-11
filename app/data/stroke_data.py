from __future__ import annotations
import os
from typing import Dict, Any, List
import pandas as pd
from flask import current_app
from app.db.mongo import get_db

AGE_BINS   = [0, 20, 30, 40, 50, 60, 70, 80, 200]
AGE_LABELS = ["<20","20–29","30–39","40–49","50–59","60–69","70–79","80+"]

BMI_BINS   = [0, 18.5, 25, 30, 35, 100]
BMI_LABELS = ["Under","Normal","Over","Obese","Severe"]

GLU_BINS   = [0, 80, 100, 125, 200, 10000]
GLU_LABELS = ["<80","80–99","100–124","125–199","200+"]

def _seed_from_csv_if_needed() -> None:
    db = get_db()
    coll = db.patients
    if coll.estimated_document_count() > 0:
        return

    csv_path = current_app.config.get("DATASET_PATH")
    if not csv_path or not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]
    df["bmi"] = pd.to_numeric(df["bmi"], errors="coerce")
    df["avg_glucose_level"] = pd.to_numeric(df["avg_glucose_level"], errors="coerce")
    if df["bmi"].isna().any():
        df["bmi"].fillna(df["bmi"].median(), inplace=True)

    docs = []
    for _, r in df.iterrows():
        docs.append({
            "_csv_id": int(r["id"]),
            "demographics": {
                "gender": str(r.get("gender", "")),
                "age": float(r.get("age", 0)),
                "ever_married": str(r.get("ever_married", "")),
                "work_type": str(r.get("work_type", "")),
                "residence_type": str(r.get("residence_type", "")),
                "smoking_status": str(r.get("smoking_status", "")).lower(),
            },
            "medical_history": {
                "hypertension": int(r.get("hypertension", 0)),
                "heart_disease": int(r.get("heart_disease", 0)),
                "avg_glucose_level": float(r.get("avg_glucose_level", 0)),
                "bmi": float(r.get("bmi", 0)),
            },
            "risk_assessment": {  # using dataset label as outcome for now
                "stroke": int(r.get("stroke", 0)),
                "risk_score": None, "category": None, "calculated_at": None
            },
            "meta": {"source": "kaggle_healthcare-stroke", "is_active": True},
        })

    if docs:
        coll.insert_many(docs)
        db.dataset_metadata.update_one(
            {"source": "kaggle_healthcare-stroke"},
            {"$set": {"source": "kaggle_healthcare-stroke"}},
            upsert=True,
        )

def _ensure_seed():
    _seed_from_csv_if_needed()

def _band_counts(field: str, bins: List[float], labels: List[str]) -> List[int]:
    # fetch all values and bin in Python (simpler/portable)
    vals = []
    for d in get_db().patients.find({}, {field: 1, "_id": 0}):
        v = d
        for k in field.split("."):
            v = v.get(k, None) if isinstance(v, dict) else None
        if v is None:
            continue
        try:
            vals.append(float(v))
        except Exception:
            pass
    counts = [0]* (len(bins)-1)
    for v in vals:
        placed = False
        for i in range(len(bins)-1):
            if bins[i] <= v < bins[i+1]:
                counts[i] += 1
                placed = True
                break
        if not placed and labels[-1].endswith("+"):
            counts[-1] += 1
    return counts

def metrics() -> Dict[str, Any]:
    _ensure_seed()
    coll = get_db().patients
    total = coll.estimated_document_count() or 0
    if total == 0:
        return {"total": 0, "pct_high": 0.0, "avg_glucose": 0.0, "avg_bmi": 0.0, "model_version": "stroke_v1"}

    # aggregate averages in Python (robust to mixed types)
    glus, bmis, strokes = [], [], []
    for d in coll.find({}, {"medical_history.avg_glucose_level":1, "medical_history.bmi":1, "risk_assessment.stroke":1}):
        mh = d.get("medical_history", {})
        gl = mh.get("avg_glucose_level", None)
        bm = mh.get("bmi", None)
        if isinstance(gl, (int, float)): glus.append(float(gl))
        if isinstance(bm, (int, float)): bmis.append(float(bm))
        ra = d.get("risk_assessment", {})
        strokes.append(int(ra.get("stroke", 0)))

    avg_glu = round(sum(glus)/len(glus),1) if glus else 0.0
    avg_bmi = round(sum(bmis)/len(bmis),1) if bmis else 0.0
    pct_high = round(100.0* (sum(strokes)/len(strokes)) if strokes else 0.0, 1)

    return {
        "total": int(total),
        "pct_high": float(pct_high),
        "avg_glucose": float(avg_glu),
        "avg_bmi": float(avg_bmi),
        "model_version": "stroke_v1",
    }

def charts_data() -> Dict[str, Any]:
    _ensure_seed()
    coll = get_db().patients

    # outcome pie
    no_stroke = coll.count_documents({"risk_assessment.stroke": 0})
    stroke = coll.count_documents({"risk_assessment.stroke": 1})
    outcome = {"labels": ["No stroke","Stroke"], "values": [no_stroke, stroke]}

    # bands
    age_counts = _band_counts("demographics.age", AGE_BINS, AGE_LABELS)
    bmi_counts = _band_counts("medical_history.bmi", BMI_BINS, BMI_LABELS)
    glu_counts = _band_counts("medical_history.avg_glucose_level", GLU_BINS, GLU_LABELS)

    return {
        "outcome": outcome,
        "age": {"labels": AGE_LABELS, "values": age_counts},
        "bmi": {"labels": BMI_LABELS, "values": bmi_counts},
        "glucose": {"labels": GLU_LABELS, "values": glu_counts},
    }
