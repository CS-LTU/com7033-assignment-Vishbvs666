'''
===========================================================
StrokeCare Web Application — Secure Software Development
Author: Vishvapriya Sangvikar

Course: COM7033 – MSc Data Science & Artificial Intelligence
Student ID: 2415083
Institution: Leeds Trinity University
Assessment: Assessment 1 – Software Artefact (70%)
AI Statement: Portions of this file were drafted or refined using
    generative AI for planning and editing only,
    as permitted in the module brief.
===========================================================
'''

# app/ml/train_model.py
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import LabelEncoder


# Resolve project base dir safely no matter where we run from
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "healthcare-dataset-stroke-data.csv"
MODEL_PATH = BASE_DIR / "instance" / "stroke_model.joblib"

RANDOM_STATE = 42


def train_balanced_model() -> None:
    """
    Train a tuned RandomForest stroke prediction model on the Kaggle dataset with
    SMOTE balancing, then save the model + label encoders as a joblib file.

    This script is intended to be run manually from the project root, e.g.:

        python -m app.ml.train_model

    or:

        python app/ml/train_model.py
    """

    # ------------------------------------------------------------------
    # 1. Load dataset
    # ------------------------------------------------------------------
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Could not find dataset at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # Handle missing BMI values (common Kaggle issue)
    df["bmi"] = df["bmi"].fillna(df["bmi"].median())

    # ------------------------------------------------------------------
    # 2. Encode categorical fields using LabelEncoder
    # ------------------------------------------------------------------
    label_cols = ["gender", "ever_married", "work_type", "Residence_type", "smoking_status"]
    encoders: dict[str, LabelEncoder] = {}

    for col in label_cols:
        enc = LabelEncoder()
        df[col] = enc.fit_transform(df[col].astype(str))
        encoders[col] = enc

    # ------------------------------------------------------------------
    # 3. Features + target
    # ------------------------------------------------------------------
    feature_cols = [
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
    ]

    X = df[feature_cols]
    y = df["stroke"].astype(int)

    # ------------------------------------------------------------------
    # 4. Fix class imbalance with SMOTE
    # ------------------------------------------------------------------
    sm = SMOTE(k_neighbors=5, random_state=RANDOM_STATE)
    X_res_arr, y_res_arr = sm.fit_resample(X.values, y.values)

    # Convert back to DataFrame/Series
    X_res = pd.DataFrame(X_res_arr, columns=feature_cols)
    y_res = pd.Series(y_res_arr, name="stroke")

    print("Before SMOTE:", y.value_counts().to_dict())
    print("After SMOTE:", y_res.value_counts().to_dict())

    # ------------------------------------------------------------------
    # 5. Train-test split
    # ------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X_res,
        y_res,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y_res,
    )

    # ------------------------------------------------------------------
    # 6. Hyperparameter tuning (RandomizedSearchCV on RandomForest)
    # ------------------------------------------------------------------
    base_rf = RandomForestClassifier(
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    # Small but meaningful search space (kept reasonable so it finishes)
    param_distributions = {
        "n_estimators": [200, 300, 400, 600],
        "max_depth": [None, 6, 10, 16, 24],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2", 0.5],
        "bootstrap": [True, False],
    }

    search = RandomizedSearchCV(
    estimator=base_rf,
    param_distributions=param_distributions,
    n_iter=20,
    scoring="roc_auc",
    n_jobs=1,              # 👈 change from -1 to 1
    cv=5,
    verbose=2,
    random_state=RANDOM_STATE,
)

    print("\n Starting RandomizedSearchCV over RandomForest hyperparameters…")
    search.fit(X_train, y_train)

    print("\nBest CV ROC-AUC:", search.best_score_)
    print(" Best params:")
    for k, v in search.best_params_.items():
        print(f"  • {k}: {v}")

    best_model: RandomForestClassifier = search.best_estimator_

    # ------------------------------------------------------------------
    # 7. Evaluation on held-out test set
    # ------------------------------------------------------------------
    preds = best_model.predict(X_test)
    proba = best_model.predict_proba(X_test)[:, 1]

    print("\nClassification Report (test set):")
    print(classification_report(y_test, preds))

    try:
        auc = roc_auc_score(y_test, proba)
        print(f"ROC-AUC (test set): {auc:.4f}")
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 8. Save model + encoders + feature order
    # ------------------------------------------------------------------
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    bundle = {
        "model": best_model,
        "encoders": encoders,
        "feature_order": feature_cols,
    }

    joblib.dump(bundle, MODEL_PATH)
    print(f"\n✔ NEW TUNED MODEL SAVED as {MODEL_PATH}")


if __name__ == "__main__":
    train_balanced_model()
