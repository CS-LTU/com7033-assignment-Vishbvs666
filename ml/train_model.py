from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score


# --------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]  # -> StrokeCare/
DATA_PATH = BASE_DIR / "data" / "healthcare-dataset-stroke-data.csv"
MODEL_PATH = BASE_DIR / "instance" / "stroke_model.joblib"
MODEL_INFO_PATH = BASE_DIR / "app" / "ml" / "model_info.json"


def main() -> None:
    print(f"Loading data from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    target_col = "stroke"
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

    df = df[feature_cols + [target_col]].copy()

    # Handle missing BMI
    df["bmi"] = df["bmi"].fillna(df["bmi"].median())

    X = df[feature_cols]
    y = df[target_col]

    numeric_features = [
        "age",
        "hypertension",
        "heart_disease",
        "avg_glucose_level",
        "bmi",
    ]
    categorical_features = [
        "gender",
        "ever_married",
        "work_type",
        "Residence_type",
        "smoking_status",
    ]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )

    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("clf", clf),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=42,
    )

    print("Training model ...")
    model.fit(X_train, y_train)

    print("Evaluating ...")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    print(classification_report(y_test, y_pred, digits=3))
    roc_auc = roc_auc_score(y_test, y_proba)
    print(f"ROC AUC: {roc_auc:.3f}")

    # ----------------------------------------------------------------
    # Save model + metadata
    # ----------------------------------------------------------------
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")

    info = {
        "feature_columns": feature_cols,
        "target_column": target_col,
        "model_type": "RandomForestClassifier",
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "metrics": {
            "roc_auc": roc_auc,
        },
    }

    MODEL_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_INFO_PATH.open("w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    print(f"Saved model info to {MODEL_INFO_PATH}")


if __name__ == "__main__":
    main()
