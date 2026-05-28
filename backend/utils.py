import re
import sys
import os

# Include the root directory to path to load preprocessor
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from ml_pipeline.nlp_preprocessor import SPAM_KEYWORDS

def extract_url_features(url: str):
    """
    Feature engineering utility for URLs.
    Extracts 13 lexical and structural features.
    MUST exactly match the training signature in train_models.py.
    """
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
    
    # Check for IP address in host
    has_ip = 1 if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url_str) else 0
    
    # Check for phishing terms in host/path
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

def scan_suspicious_keywords(text: str) -> list:
    """
    Dynamic scanner that scans the raw input text for suspicious threat indicators.
    Matches exact words from our SPAM_KEYWORDS list and other high-threat urgency markers.
    """
    if not isinstance(text, str):
        return []
        
    text_lower = text.lower()
    found_keywords = set()
    
    # Combine SPAM_KEYWORDS with other specialized threat markers
    alert_keywords = list(SPAM_KEYWORDS) + [
        "irs", "warrant", "arrest", "sheriff", "jail", "block", "locked", "compromised", 
        "suspend", "routing", "ssn", "zelle", "venmo", "gift card", "unpaid", "customs",
        "wire transfer", "login", "password", "security", "credentials", "otp", "code"
    ]
    
    for word in alert_keywords:
        # Match word boundaries or substring depending on length
        pattern = r'\b' + re.escape(word) + r'\b' if len(word) > 3 else re.escape(word)
        if re.search(pattern, text_lower):
            # Return capitalised formatted key for visual pills in UI
            found_keywords.add(word.capitalize())
            
    return sorted(list(found_keywords))
