# app/ml/train_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_balanced_model():
    # Load dataset
    df = pd.read_csv("data/healthcare-dataset-stroke-data.csv")

    # Drop rows with NaN BMI (common Kaggle issue)
    df["bmi"] = df["bmi"].fillna(df["bmi"].median())

    # Encode categorical fields
    label_cols = ["gender", "ever_married", "work_type", "Residence_type", "smoking_status"]
    encoders = {}

    for col in label_cols:
        enc = LabelEncoder()
        df[col] = enc.fit_transform(df[col].astype(str))
        encoders[col] = enc

    # Features + target
    X = df[[
        "gender", "age", "hypertension", "heart_disease",
        "ever_married", "work_type", "Residence_type",
        "avg_glucose_level", "bmi", "smoking_status"
    ]]
    y = df["stroke"]

    #  FIX IMBALANCE — SMOTE Oversampling
    sm = SMOTE(k_neighbors=5, random_state=42)
    X_res, y_res = sm.fit_resample(X, y)

    print("Before SMOTE:", y.value_counts().to_dict())
    print("After SMOTE:", pd.Series(y_res).value_counts().to_dict())

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_res, y_res, test_size=0.2, random_state=42
    )

    # Strong, medical-realistic model
    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=12,
        random_state=42,
        class_weight=None
    )

    model.fit(X_train, y_train)

    # Evaluation
    preds = model.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, preds))

    # Save model + encoders
    joblib.dump({
        "model": model,
        "encoders": encoders
    }, "stroke_model.joblib")

    print("\n✔ NEW MODEL SAVED as stroke_model.joblib")

if __name__ == "__main__":
    train_balanced_model()
