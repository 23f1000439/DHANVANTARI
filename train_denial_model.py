import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

def generate_synthetic_data(n_samples=1000):
    """
    Generates synthetic training data for claim denial prediction.
    Features mimic the 47-dim vector used in the application.
    """
    np.random.seed(42)
    
    # Feature generation (simplified names for demo)
    # 0-3: Entity Counts
    diagnosis_count = np.random.poisson(2, n_samples)
    symptom_count = np.random.poisson(3, n_samples)
    medication_count = np.random.poisson(2, n_samples)
    procedure_count = np.random.poisson(1, n_samples)
    
    # 10: Confidence Score (Mean)
    confidence_mean = np.random.beta(8, 2, n_samples) # Skewed towards high confidence
    
    # 30: Medication Alignment (Binary-ish)
    med_alignment = np.random.choice([0.0, 1.0], n_samples, p=[0.2, 0.8])
    
    # 31: ICD-11 Specificity (Float)
    icd_specificity = np.random.beta(5, 5, n_samples)
    
    # 40: Claim Amount
    amount = np.random.lognormal(8, 1, n_samples)
    
    # 42: Note Length (Binary flag > 20 words)
    note_length_flag = np.random.choice([0.0, 1.0], n_samples, p=[0.1, 0.9])

    # Construct feature matrix (N, 47)
    X = np.zeros((n_samples, 47))
    X[:, 0] = diagnosis_count
    X[:, 1] = symptom_count
    X[:, 3] = medication_count
    X[:, 10] = confidence_mean
    X[:, 30] = med_alignment
    X[:, 31] = icd_specificity
    X[:, 40] = amount
    X[:, 42] = note_length_flag
    
    # Fill random noise for embeddings (20-29) to simulate vector space
    X[:, 20:30] = np.random.rand(n_samples, 10)

    # Target Generation (Logic rule: Low med alignment OR low specificity -> High Denial)
    # Base probability
    prob_denial = 0.1 
    
    # Risk factors
    prob_denial += np.where(med_alignment == 0, 0.4, 0)
    prob_denial += np.where(icd_specificity < 0.5, 0.3, 0)
    prob_denial += np.where(confidence_mean < 0.7, 0.2, 0)
    
    # Clip probability
    prob_denial = np.clip(prob_denial, 0, 1)
    
    # Generate labels
    y = np.random.binomial(1, prob_denial)
    
    return X, y

def train_model():
    print("Generating synthetic training data...")
    X, y = generate_synthetic_data(n_samples=2000)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training XGBoost Model on {len(X_train)} samples...")
    model = xgb.XGBClassifier(
        objective='binary:logistic',
        n_estimators=100,
        learning_rate=0.1,
        max_depth=4,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {acc:.2f}")
    print(classification_report(y_test, y_pred))
    
    # Save
    os.makedirs("models", exist_ok=True)
    model_path = "models/denial_v1.joblib"
    joblib.dump(model, model_path)
    print(f"\n✅ Model saved to {model_path}")

if __name__ == "__main__":
    try:
        train_model()
    except Exception as e:
        print(f"Training Failed: {e}")
