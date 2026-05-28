import os
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

# Paths & Binds
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.database import init_db, get_db, ScanHistory, AppConfig, db_mode_str, UserFeedback
from backend.schemas import ScanRequest, ScanResponse, MetricsResponse, ConfigUpdate, ConfigResponse, PredictTextRequest, PredictUrlRequest, PredictResponse, FeedbackRequest

from backend.models.model_loader import MLModelLoader
from backend.utils import scan_suspicious_keywords

# Initialize FastAPI App
app = FastAPI(
    title="ML Fraud & Spam Detection API",
    description="Real-time multi-channel threat scanning API powered by machine learning.",
    version="1.0.0"
)

# Bind CORS to allow seamless connection from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Models on Startup
model_loader = MLModelLoader()

@app.on_event("startup")
def startup_event():
    # Setup tables in SQLite / Cloud DB
    init_db()
    print("FastAPI Backend Server started successfully.")

@app.post("/api/scan", response_model=ScanResponse)
def scan_content(request: ScanRequest, db: Session = Depends(get_db)):
    """
    Main Universal Threat Scanner. Analyzes user inputs across channels
    and writes metrics directly to the local or cloud database.
    """
    channel = request.channel.strip().upper()
    content = request.content
    
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Content cannot be empty."
        )
        
    # Supported Channels: SMS, EMAIL, CALL, URL, SCAM
    valid_channels = ["SMS", "EMAIL", "CALL", "URL", "SCAM"]
    if channel not in valid_channels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid channel. Must be one of: {', '.join(valid_channels)}"
        )
        
    try:
        prediction = "Safe"
        risk_score = 0.0
        distribution = {}
        
        # Execute dedicated model inference
        if channel == "SMS":
            prediction, risk_score, distribution = model_loader.predict_sms(content)
        elif channel == "EMAIL":
            prediction, risk_score, distribution = model_loader.predict_email(content)
        elif channel == "CALL":
            prediction, risk_score, distribution = model_loader.predict_call(content)
        elif channel == "URL":
            prediction, risk_score, distribution = model_loader.predict_url(content)
        elif channel == "SCAM":
            prediction, risk_score, distribution = model_loader.predict_scam(content)
            
        # Extract suspicious keyword highlights (text only)
        keywords = []
        if channel != "URL":
            keywords = scan_suspicious_keywords(content)
            
        # Standardize promotional category mappings (if model predicted safe, check if promotional words match)
        if prediction == "Safe" and channel in ["SMS", "EMAIL"]:
            # Check if promotional keywords dominate (e.g. promo, sale, coupon, buy)
            promo_words = ["promo", "sale", "coupon", "discount", "offer", "buy", "deal", "shop"]
            if any(w in content.lower() for w in promo_words):
                prediction = "Promotional"
                # Keep risk score low for promotional
                risk_score = min(35.0, risk_score + 15)
                distribution["Promotional"] = 0.4
                
        # Write threat entry to database
        db_history_entry = ScanHistory(
            channel=request.channel,
            input_content=content,
            prediction=prediction,
            risk_score=round(risk_score, 2),
            timestamp=datetime.utcnow(),
            db_mode=db_mode_str
        )
        
        db.add(db_history_entry)
        db.commit()
        db.refresh(db_history_entry)
        
        return ScanResponse(
            id=db_history_entry.id,
            channel=db_history_entry.channel,
            input_content=db_history_entry.input_content,
            prediction=db_history_entry.prediction,
            risk_score=db_history_entry.risk_score,
            suspicious_keywords=keywords,
            category_distribution=distribution,
            timestamp=db_history_entry.timestamp,
            db_mode=db_history_entry.db_mode
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing inference scan: {e}"
        )

@app.get("/api/history", response_model=List[ScanResponse])
def get_history(
    limit: int = 50, 
    offset: int = 0, 
    channel: str = None, 
    db: Session = Depends(get_db)
):
    """
    Retrieves all past threat scan logs from database with search bounds.
    """
    query = db.query(ScanHistory)
    if channel:
        query = query.filter(ScanHistory.channel.ilike(channel))
        
    # Sort by timestamp descending
    history = query.order_by(ScanHistory.timestamp.desc()).offset(offset).limit(limit).all()
    
    response_list = []
    for item in history:
        # Re-extract keywords on-the-fly for response display
        keywords = []
        if item.channel.upper() != "URL":
            keywords = scan_suspicious_keywords(item.input_content)
            
        response_list.append(ScanResponse(
            id=item.id,
            channel=item.channel,
            input_content=item.input_content,
            prediction=item.prediction,
            risk_score=item.risk_score,
            suspicious_keywords=keywords,
            category_distribution={}, # Static log returns empty distribution for speed
            timestamp=item.timestamp,
            db_mode=item.db_mode
        ))
    return response_list

@app.get("/api/metrics", response_model=MetricsResponse)
def get_metrics(db: Session = Depends(get_db)):
    """
    Computes system threat metrics (total logs, threat percentage, and distribution categories).
    """
    total = db.query(ScanHistory).count()
    if total == 0:
        return MetricsResponse(
            total_scans=0,
            threat_percentage=0.0,
            safe_count=0,
            threat_count=0,
            category_counts={"Safe": 0, "Spam": 0, "Scam": 0, "Fraud": 0, "Phishing": 0, "Promotional": 0}
        )
        
    safe_cnt = db.query(ScanHistory).filter(ScanHistory.prediction == "Safe").count()
    threat_cnt = total - safe_cnt
    threat_pct = (threat_cnt / total) * 100.0
    
    categories = ["Safe", "Spam", "Scam", "Fraud", "Phishing", "Promotional"]
    cat_counts = {}
    for cat in categories:
        cat_counts[cat] = db.query(ScanHistory).filter(ScanHistory.prediction == cat).count()
        
    return MetricsResponse(
        total_scans=total,
        threat_percentage=round(threat_pct, 2),
        safe_count=safe_cnt,
        threat_count=threat_cnt,
        category_counts=cat_counts
    )

@app.get("/api/settings", response_model=ConfigResponse)
def get_settings(db: Session = Depends(get_db)):
    """
    Returns active database mode.
    """
    cloud_config = db.query(AppConfig).filter(AppConfig.key == "CLOUD_DB_URI").first()
    return ConfigResponse(
        db_mode=db_mode_str,
        cloud_db_uri_configured=True if (cloud_config and cloud_config.value) else False
    )

@app.post("/api/settings")
def update_settings(payload: ConfigUpdate, db: Session = Depends(get_db)):
    """
    Updates the database configuration settings. If a cloud connection string is provided,
    saves it locally for future reload.
    """
    try:
        config_val = payload.cloud_db_uri
        db_uri = db.query(AppConfig).filter(AppConfig.key == "CLOUD_DB_URI").first()
        
        if not db_uri:
            db_uri = AppConfig(key="CLOUD_DB_URI", value=config_val)
            db.add(db_uri)
        else:
            db_uri.value = config_val
            
        db.commit()
        return {"status": "Success", "message": "Database settings updated successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {e}"
        )

# ==================== Step 8 Endpoints ====================

@app.post("/predict-sms", response_model=PredictResponse)
def predict_sms(request: PredictTextRequest, db: Session = Depends(get_db)):
    content = request.text or request.content
    if not content:
        raise HTTPException(status_code=400, detail="Text or content key is required.")
        
    pred, risk, dist = model_loader.predict_sms(content)
    conf = risk if pred in ["Spam", "Scam", "Fraud"] else (100.0 - risk)
    
    # Check promotional overrides
    promo_words = ["promo", "sale", "coupon", "discount", "offer", "buy"]
    if pred == "Safe" and any(w in content.lower() for w in promo_words):
        pred = "Promotional"
        conf = 85.0
        risk = 30.0
        
    db.add(ScanHistory(
        channel="SMS",
        input_content=content,
        prediction=pred,
        risk_score=round(risk, 2),
        timestamp=datetime.utcnow(),
        db_mode=db_mode_str
    ))
    db.commit()
    
    return PredictResponse(prediction=pred, confidence=f"{round(conf)}%")

@app.post("/predict-email", response_model=PredictResponse)
def predict_email(request: PredictTextRequest, db: Session = Depends(get_db)):
    content = request.text or request.content
    if not content:
        raise HTTPException(status_code=400, detail="Text or content key is required.")
        
    pred, risk, dist = model_loader.predict_email(content)
    conf = risk if pred in ["Spam", "Phishing", "Scam"] else (100.0 - risk)
    
    db.add(ScanHistory(
        channel="Email",
        input_content=content,
        prediction=pred,
        risk_score=round(risk, 2),
        timestamp=datetime.utcnow(),
        db_mode=db_mode_str
    ))
    db.commit()
    
    return PredictResponse(prediction=pred, confidence=f"{round(conf)}%")

@app.post("/predict-call", response_model=PredictResponse)
def predict_call(request: PredictTextRequest, db: Session = Depends(get_db)):
    content = request.text or request.content
    if not content:
        raise HTTPException(status_code=400, detail="Text or content key is required.")
        
    pred, risk, dist = model_loader.predict_call(content)
    conf = risk if pred in ["Fraud", "Scam"] else (100.0 - risk)
    
    db.add(ScanHistory(
        channel="Call",
        input_content=content,
        prediction=pred,
        risk_score=round(risk, 2),
        timestamp=datetime.utcnow(),
        db_mode=db_mode_str
    ))
    db.commit()
    
    return PredictResponse(prediction=pred, confidence=f"{round(conf)}%")

@app.post("/predict-url", response_model=PredictResponse)
def predict_url(request: PredictUrlRequest, db: Session = Depends(get_db)):
    content = request.url
    if not content:
        raise HTTPException(status_code=400, detail="url key is required.")
        
    pred, risk, dist = model_loader.predict_url(content)
    conf = risk if pred == "Phishing" else (100.0 - risk)
    
    db.add(ScanHistory(
        channel="URL",
        input_content=content,
        prediction=pred,
        risk_score=round(risk, 2),
        timestamp=datetime.utcnow(),
        db_mode=db_mode_str
    ))
    db.commit()
    
    return PredictResponse(prediction=pred, confidence=f"{round(conf)}%")


@app.post("/api/feedback")
def submit_feedback(
    payload: FeedbackRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Submits user feedback or label corrections for threat scanning.
    Logs feedback, updates scan history, and retrains the ML model in the background.
    """
    scan_id = payload.scan_id
    corrected_prediction = payload.corrected_prediction.strip()
    
    # 1. Fetch scan history
    history_entry = db.query(ScanHistory).filter(ScanHistory.id == scan_id).first()
    if not history_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan history record with ID #{scan_id} not found."
        )
        
    # Standardize predictions
    valid_predictions = ["Safe", "Spam", "Scam", "Fraud", "Phishing", "Promotional"]
    if corrected_prediction not in valid_predictions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid label. Must be one of: {', '.join(valid_predictions)}"
        )
        
    try:
        # 2. Add entry to UserFeedback table
        feedback_entry = UserFeedback(
            scan_history_id=scan_id,
            channel=history_entry.channel,
            input_content=history_entry.input_content,
            original_prediction=history_entry.prediction,
            corrected_prediction=corrected_prediction
        )
        db.add(feedback_entry)
        
        # 3. Direct Calibration: Update history entry prediction & risk score
        history_entry.prediction = corrected_prediction
        # Recalibrate risk score
        if corrected_prediction == "Safe":
            history_entry.risk_score = 5.0
        elif corrected_prediction == "Promotional":
            history_entry.risk_score = 25.0
        else:
            history_entry.risk_score = 95.0
            
        db.commit()
        
        # 4. Trigger active continuous retraining in a background task
        background_tasks.add_task(
            model_loader.retrain_model,
            channel=history_entry.channel,
            content=history_entry.input_content,
            corrected_label=corrected_prediction
        )
        
        return {
            "status": "Success",
            "message": "Feedback submitted successfully. Model retraining started in the background.",
            "corrected_prediction": corrected_prediction,
            "new_risk_score": history_entry.risk_score
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {e}"
        )


