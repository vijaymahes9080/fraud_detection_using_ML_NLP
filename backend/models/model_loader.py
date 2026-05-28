import os
import pickle
import numpy as np
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "backend", "saved_models")

# Include the root directory to path to load preprocessor
sys.path.insert(0, BASE_DIR)
from ml_pipeline.nlp_preprocessor import clean_text
from backend.utils import extract_url_features
from backend.models.security_utils import verify_signature


class MLModelLoader:
    """
    Singleton wrapper to load serialized Scikit-learn models and perform real-time security predictions.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MLModelLoader, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self.models = {}
        self.vectorizers = {}
        self._load_all_models()
        self._initialized = True
        
    def _load_all_models(self):
        print("Initializing Machine Learning Models...")
        
        # 1. SMS Model
        self._load_pipeline("sms", "sms_model.pkl", "sms_vectorizer.pkl")
        
        # 2. Email Model
        self._load_pipeline("email", "email_model.pkl", "email_vectorizer.pkl")
        
        # 3. Call Model
        self._load_pipeline("call", "call_model.pkl", "call_vectorizer.pkl")
        
        # 4. URL Model
        self._load_model_only("url", "url_model.pkl")
        
        # 5. Scam Model
        self._load_pipeline("scam", "scam_model.pkl", "scam_vectorizer.pkl")
        
        print("ML Models fully loaded.")
        
    def _load_pipeline(self, name, model_file, vec_file):
        model_path = os.path.join(SAVED_MODELS_DIR, model_file)
        vec_path = os.path.join(SAVED_MODELS_DIR, vec_file)
        
        if os.path.exists(model_path) and os.path.exists(vec_path):
            try:
                # Cryptographically verify signatures before opening and deserializing the files
                verify_signature(model_path)
                verify_signature(vec_path)
                
                with open(model_path, "rb") as f:
                    self.models[name] = pickle.load(f)
                with open(vec_path, "rb") as f:
                    self.vectorizers[name] = pickle.load(f)
                print(f"Loaded TF-IDF model pipeline for: {name}")
            except Exception as e:
                print(f"Error loading model pipeline for {name}: {e}. Fallback active.")
        else:
            print(f"Binary not found for {name} ({model_file}/{vec_file}). Running on rules-engine fallback.")
            
    def _load_model_only(self, name, model_file):
        model_path = os.path.join(SAVED_MODELS_DIR, model_file)
        if os.path.exists(model_path):
            try:
                # Cryptographically verify signature before opening and deserializing the file
                verify_signature(model_path)
                
                with open(model_path, "rb") as f:
                    self.models[name] = pickle.load(f)
                print(f"Loaded model binary for: {name}")
            except Exception as e:
                print(f"Error loading model binary for {name}: {e}. Fallback active.")
        else:
            print(f"Binary not found for {name} ({model_file}). Running on rules-engine fallback.")

    def predict_sms(self, text: str):
        cleaned = clean_text(text)
        if "sms" in self.models and "sms" in self.vectorizers:
            try:
                vec = self.vectorizers["sms"].transform([cleaned])
                pred = self.models["sms"].predict(vec)[0]
                proba = self.models["sms"].predict_proba(vec)[0]
                classes = self.models["sms"].classes_
                
                dist = {classes[i]: float(proba[i]) for i in range(len(classes))}
                risk = float(dist.get("Spam", 0.0)) * 100
                return pred, risk, dist
            except Exception as e:
                print(f"SMS Inference error: {e}")
                
        # Rule-based fallback
        is_spam = any(w in cleaned for w in ["win", "free", "urgent", "claim", "prize", "cash"])
        pred = "Spam" if is_spam else "Safe"
        risk = 85.0 if is_spam else 5.0
        return pred, risk, {"Safe": 1.0 - (risk/100), "Spam": risk/100}

    def predict_email(self, text: str):
        cleaned = clean_text(text)
        if "email" in self.models and "email" in self.vectorizers:
            try:
                vec = self.vectorizers["email"].transform([cleaned])
                pred = self.models["email"].predict(vec)[0]
                proba = self.models["email"].predict_proba(vec)[0]
                classes = self.models["email"].classes_
                
                dist = {classes[i]: float(proba[i]) for i in range(len(classes))}
                risk = float(dist.get("Spam", 0.0)) * 100
                return pred, risk, dist
            except Exception as e:
                print(f"Email Inference error: {e}")
                
        # Rule-based fallback
        is_spam = any(w in cleaned for w in ["pharmacy", "pill", "viagra", "suspend", "verify", "link"])
        pred = "Spam" if is_spam else "Safe"
        risk = 90.0 if is_spam else 8.0
        return pred, risk, {"Safe": 1.0 - (risk/100), "Spam": risk/100}

    def predict_call(self, text: str):
        cleaned = clean_text(text)
        if "call" in self.models and "call" in self.vectorizers:
            try:
                vec = self.vectorizers["call"].transform([cleaned])
                pred = self.models["call"].predict(vec)[0]
                proba = self.models["call"].predict_proba(vec)[0]
                classes = self.models["call"].classes_
                
                dist = {classes[i]: float(proba[i]) for i in range(len(classes))}
                
                # Risk is probability of Fraud/Scam classes combined
                risk = float(dist.get("Fraud", 0.0) + dist.get("Scam", 0.0)) * 100
                return pred, risk, dist
            except Exception as e:
                print(f"Call Inference error: {e}")
                
        # Rule-based fallback
        is_threat = any(w in cleaned for w in ["warrant", "arrest", "irs", "police", "jail", "gift card"])
        pred = "Fraud" if is_threat else "Safe"
        risk = 95.0 if is_threat else 4.0
        return pred, risk, {"Safe": 1.0 - (risk/100), "Fraud": risk/100, "Scam": 0.0}

    def predict_url(self, url: str):
        features = extract_url_features(url)
        if "url" in self.models:
            try:
                features_arr = np.array([features])
                pred = self.models["url"].predict(features_arr)[0]
                proba = self.models["url"].predict_proba(features_arr)[0]
                classes = self.models["url"].classes_
                
                dist = {classes[i]: float(proba[i]) for i in range(len(classes))}
                risk = float(dist.get("Phishing", 0.0)) * 100
                return pred, risk, dist
            except Exception as e:
                print(f"URL Inference error: {e}")
                
        # Rule-based fallback
        is_phish = features[5] == 1 or features[4] > 3 or features[6] == 0  # has sensitive word, has many slashes, or is http
        pred = "Phishing" if is_phish else "Safe"
        risk = 80.0 if is_phish else 10.0
        return pred, risk, {"Safe": 1.0 - (risk/100), "Phishing": risk/100}

    def predict_scam(self, text: str):
        cleaned = clean_text(text)
        if "scam" in self.models and "scam" in self.vectorizers:
            try:
                vec = self.vectorizers["scam"].transform([cleaned])
                pred = self.models["scam"].predict(vec)[0]
                proba = self.models["scam"].predict_proba(vec)[0]
                classes = self.models["scam"].classes_
                
                dist = {classes[i]: float(proba[i]) for i in range(len(classes))}
                risk = float(dist.get("Scam", 0.0)) * 100
                return pred, risk, dist
            except Exception as e:
                print(f"Scam Inference error: {e}")
                
        # Rule-based fallback
        is_scam = any(w in cleaned for w in ["winner", "lottery", "crypto", "bitcoin", "inherit", "gift"])
        pred = "Scam" if is_scam else "Safe"
        risk = 85.0 if is_scam else 6.0
        return pred, risk, {"Safe": 1.0 - (risk/100), "Scam": risk/100}

    def reload_model(self, name: str):
        """
        Hot-reloads a single model pipeline or model binary securely from disk.
        """
        name = name.lower()
        print(f"Hot-reloading model for: {name}...")
        if name == "sms":
            self._load_pipeline("sms", "sms_model.pkl", "sms_vectorizer.pkl")
        elif name == "email":
            self._load_pipeline("email", "email_model.pkl", "email_vectorizer.pkl")
        elif name == "call":
            self._load_pipeline("call", "call_model.pkl", "call_vectorizer.pkl")
        elif name == "url":
            self._load_model_only("url", "url_model.pkl")
        elif name == "scam":
            self._load_pipeline("scam", "scam_model.pkl", "scam_vectorizer.pkl")
        print(f"Model {name} hot-reloaded successfully.")

    def retrain_model(self, channel: str, content: str, corrected_label: str):
        """
        Appends user feedback to dataset, retrains the model on the updated dataset,
        saves the binary pickles, signs them cryptographically, and hot-reloads them.
        """
        channel_upper = channel.upper()
        print(f"Starting real-time continuous learning for channel: {channel_upper}")
        
        import pandas as pd
        import csv
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import RandomForestClassifier
        from backend.models.security_utils import sign_file
        
        dataset_base = os.path.join(BASE_DIR, "ml_pipeline", "dataset")
        
        # 1. Append the feedback sample to the correct CSV file
        if channel_upper == "SMS":
            csv_path = os.path.join(dataset_base, "sms", "sms.csv")
            new_row = {"text": content, "label": corrected_label}
            cols = ["text", "label"]
        elif channel_upper == "EMAIL":
            csv_path = os.path.join(dataset_base, "email", "email.csv")
            new_row = {"text": content, "label": corrected_label}
            cols = ["text", "label"]
        elif channel_upper == "CALL":
            csv_path = os.path.join(dataset_base, "calls", "calls.csv")
            new_row = {"text": content, "label": corrected_label}
            cols = ["text", "label"]
        elif channel_upper == "SCAM":
            csv_path = os.path.join(dataset_base, "scam", "scam.csv")
            new_row = {"text": content, "label": corrected_label}
            cols = ["text", "label"]
        elif channel_upper == "URL":
            csv_path = os.path.join(dataset_base, "phishing", "phishing.csv")
            new_row = {"url": content, "label": corrected_label}
            cols = ["url", "label"]
        else:
            raise ValueError(f"Invalid channel: {channel}")
            
        # Append to CSV securely
        if os.path.exists(csv_path):
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writerow(new_row)
            print(f"Appended feedback row to {os.path.basename(csv_path)}")
        else:
            # If CSV doesn't exist, create it
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writeheader()
                writer.writerow(new_row)
            print(f"Created new dataset CSV and wrote feedback row to {os.path.basename(csv_path)}")
            
        # 2. Retrain model based on updated CSV
        df = pd.read_csv(csv_path)
        
        if channel_upper in ["SMS", "EMAIL", "CALL", "SCAM"]:
            df = df.dropna(subset=['text', 'label'])
            df['clean_text'] = df['text'].apply(clean_text)
            df = df[df['clean_text'].str.strip() != ""]
            
            X = df['clean_text']
            y = df['label']
            
            # Setup vectorizer configurations
            if channel_upper == "SMS":
                max_features, ngram_range = 2500, (1, 2)
                vec_file, model_file = "sms_vectorizer.pkl", "sms_model.pkl"
            elif channel_upper == "EMAIL":
                max_features, ngram_range = 5000, (1, 2)
                vec_file, model_file = "email_vectorizer.pkl", "email_model.pkl"
            elif channel_upper == "CALL":
                max_features, ngram_range = 1500, (1, 2)
                vec_file, model_file = "call_vectorizer.pkl", "call_model.pkl"
            elif channel_upper == "SCAM":
                max_features, ngram_range = 2500, (1, 2)
                vec_file, model_file = "scam_vectorizer.pkl", "scam_model.pkl"
                
            vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=ngram_range)
            X_vec = vectorizer.fit_transform(X)
            
            model = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced')
            model.fit(X_vec, y)
            
            # Save files
            vec_path = os.path.join(SAVED_MODELS_DIR, vec_file)
            model_path = os.path.join(SAVED_MODELS_DIR, model_file)
            
            with open(vec_path, "wb") as f:
                pickle.dump(vectorizer, f)
            with open(model_path, "wb") as f:
                pickle.dump(model, f)
                
            # Cryptographically sign
            sign_file(vec_path)
            sign_file(model_path)
            
        elif channel_upper == "URL":
            df = df.dropna(subset=['url', 'label'])
            urls = df['url'].tolist()
            y = df['label']
            
            features = [extract_url_features(url) for url in urls]
            X = np.array(features)
            
            model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, class_weight='balanced')
            model.fit(X, y)
            
            model_path = os.path.join(SAVED_MODELS_DIR, "url_model.pkl")
            with open(model_path, "wb") as f:
                pickle.dump(model, f)
                
            # Cryptographically sign
            sign_file(model_path)
            
        # 3. Reload in-memory
        self.reload_model(channel_upper)
        print(f"Continuous learning completed successfully for channel {channel_upper}!")

