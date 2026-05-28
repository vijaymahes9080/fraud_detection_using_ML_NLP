import os
import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Import the NLP Preprocessor
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml_pipeline.nlp_preprocessor import clean_text
from backend.models.security_utils import sign_file


# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "ml_pipeline", "dataset")
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "backend", "saved_models")
os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

def train_sms_classifier():
    print("\n--- Training SMS Spam/Safe Classifier with Preprocessing ---")
    path = os.path.join(DATASET_DIR, "sms", "sms.csv")
    if not os.path.exists(path):
        print(f"Dataset not found at {path}. Skipping.")
        return
        
    df = pd.read_csv(path)
    df = df.dropna(subset=['text', 'label'])
    
    print("Applying NLP preprocessing...")
    df['clean_text'] = df['text'].apply(clean_text)
    
    # Filter empty texts after cleaning
    df = df[df['clean_text'].str.strip() != ""]
    
    X = df['clean_text']
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    model = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced')
    model.fit(X_train_vec, y_train)
    
    preds = model.predict(X_test_vec)
    print(f"Accuracy: {accuracy_score(y_test, preds):.4f}")
    print("Classification Report:")
    print(classification_report(y_test, preds))
    
    # Train on full data and save
    X_full_vec = vectorizer.fit_transform(X)
    model.fit(X_full_vec, y)
    
    vec_path = os.path.join(SAVED_MODELS_DIR, "sms_vectorizer.pkl")
    model_path = os.path.join(SAVED_MODELS_DIR, "sms_model.pkl")
    with open(vec_path, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    sign_file(vec_path)
    sign_file(model_path)
    print("SMS Model saved and signed successfully.")

def train_email_classifier():
    print("\n--- Training Email Spam/Safe Classifier with Preprocessing ---")
    path = os.path.join(DATASET_DIR, "email", "email.csv")
    if not os.path.exists(path):
        print(f"Dataset not found at {path}. Skipping.")
        return
        
    df = pd.read_csv(path)
    df = df.dropna(subset=['text', 'label'])
    
    print("Applying NLP preprocessing...")
    df['clean_text'] = df['text'].apply(clean_text)
    df = df[df['clean_text'].str.strip() != ""]
    
    X = df['clean_text']
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    model = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced')
    model.fit(X_train_vec, y_train)
    
    preds = model.predict(X_test_vec)
    print(f"Accuracy: {accuracy_score(y_test, preds):.4f}")
    print("Classification Report:")
    print(classification_report(y_test, preds))
    
    # Train on full data and save
    X_full_vec = vectorizer.fit_transform(X)
    model.fit(X_full_vec, y)
    
    vec_path = os.path.join(SAVED_MODELS_DIR, "email_vectorizer.pkl")
    model_path = os.path.join(SAVED_MODELS_DIR, "email_model.pkl")
    with open(vec_path, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    sign_file(vec_path)
    sign_file(model_path)
    print("Email Model saved and signed successfully.")

def train_call_classifier():
    print("\n--- Training Call Transcript Fraud/Scam/Safe Classifier with Preprocessing ---")
    path = os.path.join(DATASET_DIR, "calls", "calls.csv")
    if not os.path.exists(path):
        print(f"Dataset not found at {path}. Skipping.")
        return
        
    df = pd.read_csv(path)
    df = df.dropna(subset=['text', 'label'])
    
    print("Applying NLP preprocessing...")
    df['clean_text'] = df['text'].apply(clean_text)
    df = df[df['clean_text'].str.strip() != ""]
    
    X = df['clean_text']
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    vectorizer = TfidfVectorizer(max_features=1500, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    model = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced')
    model.fit(X_train_vec, y_train)
    
    preds = model.predict(X_test_vec)
    print(f"Accuracy: {accuracy_score(y_test, preds):.4f}")
    print("Classification Report:")
    print(classification_report(y_test, preds))
    
    # Train on full data and save
    X_full_vec = vectorizer.fit_transform(X)
    model.fit(X_full_vec, y)
    
    vec_path = os.path.join(SAVED_MODELS_DIR, "call_vectorizer.pkl")
    model_path = os.path.join(SAVED_MODELS_DIR, "call_model.pkl")
    with open(vec_path, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    sign_file(vec_path)
    sign_file(model_path)
    print("Call Model saved and signed successfully.")

def extract_url_features(url):
    url_str = str(url).lower()
    length = len(url_str)
    
    qty_dot = url_str.count('.')
    qty_hyphen = url_str.count('-')
    qty_underline = url_str.count('_')
    qty_slash = url_str.count('/')
    qty_question = url_str.count('?')
    qty_equal = url_str.count('=')
    qty_at = url_str.count('@')
    qty_digits = sum(c.isdigit() for c in url_str)
    qty_letters = sum(c.isalpha() for c in url_str)
    
    import re
    has_ip = 1 if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url_str) else 0
    
    sensitive_words = ["login", "verify", "secure", "update", "paypal", "netflix", "bank", "account", "signin", "chase", "amazon"]
    has_sensitive = 0
    for word in sensitive_words:
        if word in url_str:
            has_sensitive = 1
            break
            
    is_https = 1 if url_str.startswith("https") else 0
    
    return [
        length, qty_dot, qty_hyphen, qty_underline, qty_slash, 
        qty_question, qty_equal, qty_at, qty_digits, qty_letters, 
        has_ip, has_sensitive, is_https
    ]

def train_url_classifier():
    print("\n--- Training Phishing URL Classifier ---")
    path = os.path.join(DATASET_DIR, "phishing", "phishing.csv")
    if not os.path.exists(path):
        print(f"Dataset not found at {path}. Skipping.")
        return
        
    df = pd.read_csv(path)
    df = df.dropna(subset=['url', 'label'])
    
    urls = df['url'].tolist()
    y = df['label']
    
    features = [extract_url_features(url) for url in urls]
    X = np.array(features)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, preds):.4f}")
    print("Classification Report:")
    print(classification_report(y_test, preds))
    
    # Train on full data and save
    model.fit(X, y)
    
    model_path = os.path.join(SAVED_MODELS_DIR, "url_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    sign_file(model_path)
    print("URL Model saved and signed successfully.")

def train_scam_classifier():
    print("\n--- Training Scam/Fraud Message Classifier with Preprocessing ---")
    path = os.path.join(DATASET_DIR, "scam", "scam.csv")
    if not os.path.exists(path):
        print(f"Dataset not found at {path}. Skipping.")
        return
        
    df = pd.read_csv(path)
    df = df.dropna(subset=['text', 'label'])
    
    print("Applying NLP preprocessing...")
    df['clean_text'] = df['text'].apply(clean_text)
    df = df[df['clean_text'].str.strip() != ""]
    
    X = df['clean_text']
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    model = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced')
    model.fit(X_train_vec, y_train)
    
    preds = model.predict(X_test_vec)
    print(f"Accuracy: {accuracy_score(y_test, preds):.4f}")
    print("Classification Report:")
    print(classification_report(y_test, preds))
    
    # Train on full data and save
    X_full_vec = vectorizer.fit_transform(X)
    model.fit(X_full_vec, y)
    
    vec_path = os.path.join(SAVED_MODELS_DIR, "scam_vectorizer.pkl")
    model_path = os.path.join(SAVED_MODELS_DIR, "scam_model.pkl")
    with open(vec_path, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    sign_file(vec_path)
    sign_file(model_path)
    print("Scam Model saved and signed successfully.")

if __name__ == "__main__":
    print("================== Starting Model Training Pipeline ==================")
    train_sms_classifier()
    train_email_classifier()
    train_call_classifier()
    train_url_classifier()
    train_scam_classifier()
    print("\n================== All Models Trained & Saved successfully! ==================")
