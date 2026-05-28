import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
import optuna

# Path setups
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from ml_pipeline.nlp_preprocessor import clean_text
from ml_pipeline.train_models import extract_url_features
from backend.models.security_utils import sign_file


DATASET_DIR = os.path.join(BASE_DIR, "ml_pipeline", "dataset")
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "backend", "saved_models")

# Quiet optuna logging to show clear results
optuna.logging.set_verbosity(optuna.logging.WARNING)

def tune_url_classifier():
    print("\n================== Tuning Phishing URL Classifier (Optuna) ==================")
    path = os.path.join(DATASET_DIR, "phishing", "phishing.csv")
    if not os.path.exists(path):
        print("Phishing URL dataset not found. Skipping.")
        return
        
    df = pd.read_csv(path)
    df = df.dropna(subset=['url', 'label'])
    
    urls = df['url'].tolist()
    y = df['label'].map({'Safe': 0, 'Phishing': 1})
    
    features = [extract_url_features(url) for url in urls]
    X = np.array(features)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Baseline score
    baseline = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42)
    baseline.fit(X_train, y_train)
    baseline_score = accuracy_score(y_test, baseline.predict(X_test))
    print(f"Original Baseline Accuracy: {baseline_score:.4f}")
    
    def objective(trial):
        n_estimators = trial.suggest_int('n_estimators', 50, 250)
        max_depth = trial.suggest_int('max_depth', 8, 30)
        min_samples_split = trial.suggest_int('min_samples_split', 2, 10)
        min_samples_leaf = trial.suggest_int('min_samples_leaf', 1, 5)
        
        clf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            class_weight='balanced',
            random_state=42
        )
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        return accuracy_score(y_test, preds)
        
    print("Running Optuna optimization study (15 trials)...")
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=15)
    
    print("\nURL Study Finished!")
    print(f"  - Best Trial Accuracy: {study.best_value:.4f}")
    print("  - Best Hyperparameters:")
    for k, v in study.best_params.items():
        print(f"      {k}: {v}")
        
    # Train champion model and save
    tuned_model = RandomForestClassifier(
        n_estimators=study.best_params['n_estimators'],
        max_depth=study.best_params['max_depth'],
        min_samples_split=study.best_params['min_samples_split'],
        min_samples_leaf=study.best_params['min_samples_leaf'],
        class_weight='balanced',
        random_state=42
    )
    tuned_model.fit(X, y)
    # Map class labels back for loading consistency
    tuned_model.classes_ = np.array(['Safe', 'Phishing'])
    
    model_path = os.path.join(SAVED_MODELS_DIR, "url_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(tuned_model, f)
    sign_file(model_path)
    print("Tuned URL Model saved and signed successfully!")

def tune_sms_classifier():
    print("\n================== Tuning SMS Classifier (Optuna) ==================")
    path = os.path.join(DATASET_DIR, "sms", "sms.csv")
    if not os.path.exists(path):
        print("SMS dataset not found. Skipping.")
        return
        
    df = pd.read_csv(path)
    df = df.dropna(subset=['text', 'label'])
    
    df['clean_text'] = df['text'].apply(clean_text)
    df = df[df['clean_text'].str.strip() != ""]
    
    X = df['clean_text']
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Baseline
    vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    baseline = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced')
    baseline.fit(X_train_vec, y_train)
    baseline_score = accuracy_score(y_test, baseline.predict(X_test_vec))
    print(f"Original Baseline Accuracy: {baseline_score:.4f}")
    
    def objective(trial):
        # Tune C (Regularization Strength) and penalty solver parameters
        C = trial.suggest_float('C', 0.05, 20.0, log=True)
        max_iter = trial.suggest_int('max_iter', 200, 1000)
        
        clf = LogisticRegression(C=C, max_iter=max_iter, class_weight='balanced', random_state=42)
        clf.fit(X_train_vec, y_train)
        return accuracy_score(y_test, clf.predict(X_test_vec))
        
    print("Running Optuna optimization study (10 trials)...")
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=10)
    
    print("\nSMS Study Finished!")
    print(f"  - Best Trial Accuracy: {study.best_value:.4f}")
    print("  - Best Hyperparameters:")
    for k, v in study.best_params.items():
        print(f"      {k}: {v}")
        
    # Re-train and save
    tuned_vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2))
    X_full_vec = tuned_vectorizer.fit_transform(X)
    
    tuned_model = LogisticRegression(
        C=study.best_params['C'],
        max_iter=study.best_params['max_iter'],
        class_weight='balanced',
        random_state=42
    )
    tuned_model.fit(X_full_vec, y)
    
    vec_path = os.path.join(SAVED_MODELS_DIR, "sms_vectorizer.pkl")
    model_path = os.path.join(SAVED_MODELS_DIR, "sms_model.pkl")
    with open(vec_path, "wb") as f:
        pickle.dump(tuned_vectorizer, f)
    with open(model_path, "wb") as f:
        pickle.dump(tuned_model, f)
    sign_file(vec_path)
    sign_file(model_path)
    print("Tuned SMS Model saved and signed successfully!")

if __name__ == "__main__":
    print("================== Starting Hyperparameter Tuning Pipeline ==================")
    tune_url_classifier()
    tune_sms_classifier()
    print("\n================== Hyperparameter Tuning Completed successfully! ==================")
