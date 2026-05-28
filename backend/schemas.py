from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Optional

class ScanRequest(BaseModel):
    channel: str = Field(..., description="Message channel: SMS, Email, Call, URL, Scam")
    content: str = Field(..., description="The raw content (text, transript, or URL) to scan")

class ScanResponse(BaseModel):
    id: Optional[int] = None
    channel: str
    input_content: str
    prediction: str
    risk_score: float
    suspicious_keywords: List[str] = []
    category_distribution: Dict[str, float] = {}
    timestamp: datetime
    db_mode: str

    class Config:
        from_attributes = True

class MetricsResponse(BaseModel):
    total_scans: int
    threat_percentage: float
    safe_count: int
    threat_count: int
    category_counts: Dict[str, int]

class ConfigUpdate(BaseModel):
    cloud_db_uri: Optional[str] = None

class ConfigResponse(BaseModel):
    db_mode: str
    cloud_db_uri_configured: bool

# Step 8 Endpoint Schemas
class PredictTextRequest(BaseModel):
    text: Optional[str] = None
    content: Optional[str] = None

class PredictUrlRequest(BaseModel):
    url: str

class PredictResponse(BaseModel):
    prediction: str
    confidence: str

class FeedbackRequest(BaseModel):
    scan_id: int
    corrected_prediction: str


