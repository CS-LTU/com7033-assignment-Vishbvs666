from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd

# -------------------------------------------------------------------
# Paths & simple caches
# -------------------------------------------------------------------

# project_root / app / ml / model.py → project_root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INSTANCE_DIR = PROJECT_ROOT / "instance"
MODEL_PATH = INSTANCE_DIR / "stroke_model.joblib"
MODEL_INFO_PATH = Path(__file__).resolve().parent / "model_info.json"

_model_cache: Any | None = None
_model_info_cache: Dict[str, Any] | None = None


# -------------------------------------------------------------------
# Load model + metadata
# -------------------------------------------------------------------
def load_model() -> Any:
    """
    Load the trained sklearn model from instance/stroke_model.joblib.
    Uses a simple in-memory cache so we don't hit disk every request.
    """
    global _model_cache

    if _model_cache is None:
        if not MODEL_PATH.exists():
            raise RuntimeError(
                f"Model file not found at {MODEL_PATH}. "
                "Run `python -m ml.train_model` from the project root first."
            )
        _model_cache = joblib.load(MODEL_PATH)

    return _model_cache


def get_model_info() -> Dict[str, Any]:
    """
    Return metadata about the trained model:
    - feature_columns
    - metrics
    - trained_at
    """
    global _model_info_cache

    if _model_info_cache is None:
        if not MODEL_INFO_PATH.exists():
            # Not fatal, but prediction won't know feature order
            _model_info_cache = {}
        else:
            with MODEL_INFO_PATH.open("r", encoding="utf-8") as f:
                _model_info_cache = json.load(f)

    # At this point we've guaranteed it's a dict, not None (for type checkers)
    assert isinstance(_model_info_cache, dict)
    return _model_info_cache


# -------------------------------------------------------------------
# High-level predict API used by the Flask routes
# -------------------------------------------------------------------
def predict_risk(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run stroke-risk prediction.

    `features` is a dict with the 11 Kaggle fields (except id), e.g.:

        {
          "gender": "Male",
          "age": 45,
          "hypertension": 0,
          "heart_disease": 1,
          "ever_married": "Yes",
          "work_type": "Private",
          "Residence_type": "Urban",
          "avg_glucose_level": 105.3,
          "bmi": 27.5,
          "smoking_status": "formerly smoked",
        }

    Returns a dictionary like:

        {
          "probability": 0.73,
          "stroke_flag": 1,
          "risk_level": "High",
        }
    """
    model = load_model()
    info = get_model_info()

    # 1) figure out the correct column order
    feature_cols: List[str] = info.get(
        "feature_columns",
        [
            "gender",
            "age",
            "hypertension",
            "heart_disease",
            "ever_married",
            "work_type",
            "Residence_type",
            "avg_glucose_level",
            "bmi",
            "smoking_status",
        ],
    )

    # 2) build a one-row DataFrame in that order
    row = {col: features.get(col) for col in feature_cols}
    X = pd.DataFrame([row])

    # 3) get probability of stroke=1 (positive class)
    proba = float(model.predict_proba(X)[0][1])
    stroke_flag = int(proba >= 0.5)

    # 4) simple bucketing into Low / Medium / High
    if proba < 0.33:
        risk_level = "Low"
    elif proba < 0.66:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "probability": proba,
        "stroke_flag": stroke_flag,
        "risk_level": risk_level,
    }
