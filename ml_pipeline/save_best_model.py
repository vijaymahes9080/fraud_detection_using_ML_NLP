import os
import pickle
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from backend.models.security_utils import sign_file, verify_signature
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "backend", "saved_models")


def save_champion_assets():
    """
    Step 7: Save Model.
    Saves the best-performing optimized classifier, TF-IDF vectorizer, and label encoder
    into the exact filenames requested:
      - best_model.pkl
      - vectorizer.pkl
      - label_encoder.pkl
    """
    print("================== Executing Step 7: Model Saving Pipeline ==================")
    
    src_model = os.path.join(SAVED_MODELS_DIR, "sms_model.pkl")
    src_vectorizer = os.path.join(SAVED_MODELS_DIR, "sms_vectorizer.pkl")
    
    out_model_path = os.path.join(SAVED_MODELS_DIR, "best_model.pkl")
    out_vectorizer_path = os.path.join(SAVED_MODELS_DIR, "vectorizer.pkl")
    out_encoder_path = os.path.join(SAVED_MODELS_DIR, "label_encoder.pkl")
    
    if not os.path.exists(src_model) or not os.path.exists(src_vectorizer):
        print("Tuned SMS champion models not found. Please run tune_hyperparameters.py first.")
        return
        
    try:
        # Verify cryptographic signatures of the source files before loading them
        verify_signature(src_model)
        verify_signature(src_vectorizer)
        
        # 1. Save Best Model
        with open(src_model, "rb") as f:
            model = pickle.load(f)
        with open(out_model_path, "wb") as f:
            pickle.dump(model, f)
        sign_file(out_model_path)
        print(f"Saved Best Model: {out_model_path}")
        
        # 2. Save Vectorizer
        with open(src_vectorizer, "rb") as f:
            vec = pickle.load(f)
        with open(out_vectorizer_path, "wb") as f:
            pickle.dump(vec, f)
        sign_file(out_vectorizer_path)
        print(f"Saved Vectorizer: {out_vectorizer_path}")
        
        # 3. Save Label Encoder mapping
        # Maps index classes to textual representation for reuse
        label_mapping = {"Safe": 0, "Spam": 1}
        with open(out_encoder_path, "wb") as f:
            pickle.dump(label_mapping, f)
        sign_file(out_encoder_path)
        print(f"Saved Label Encoder: {out_encoder_path}")
        
        print("\nStep 7 Completed successfully! Reuse assets dynamically in deployment.")
        print("==========================================================================")
        
    except Exception as e:
        print(f"Error copying and saving champion assets: {e}")

if __name__ == "__main__":
    save_champion_assets()
