import re
import string

# Fallback English Stopwords list
FALLBACK_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "arent", "as", "at", 
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "cant", "cannot", "could", 
    "couldnt", "did", "didnt", "do", "does", "doesnt", "doing", "dont", "down", "during", "each", "few", "for", "from", 
    "further", "had", "hadnt", "has", "hasnt", "have", "havent", "having", "he", "hed", "hell", "hes", "her", "here", 
    "heres", "hers", "herself", "him", "himself", "his", "how", "hows", "i", "id", "ill", "im", "ive", "if", "in", 
    "into", "is", "isnt", "it", "its", "itself", "lets", "me", "more", "most", "mustnt", "my", "myself", "no", "nor", 
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", 
    "same", "shant", "she", "shed", "shell", "shes", "should", "shouldnt", "so", "some", "such", "than", "that", "thats", 
    "the", "their", "theirs", "them", "themselves", "then", "there", "theres", "these", "they", "theyd", "theyll", 
    "theyre", "theyve", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasnt", "we", 
    "wed", "well", "were", "weve", "werent", "what", "whats", "when", "whens", "where", "wheres", "which", "while", 
    "who", "whos", "whom", "why", "whys", "with", "wont", "would", "wouldnt", "you", "youd", "youll", "youre", "youve", 
    "your", "yours", "yourself", "yourselves", "now", "and"
}

# High-Risk Spam Keywords list for Feature Engineering
SPAM_KEYWORDS = [
    "win", "free", "urgent", "claim", "congratulations", "cash", "prize", "viagra", "cialis", 
    "bitcoin", "crypto", "irs", "bail", "gift card", "suspend", "restricted", "unauthorized", 
    "account", "verify", "update", "login", "winner", "limited", "loan", "off", "guaranteed", "alert"
]

# Attempt to load NLTK resources
NLTK_AVAILABLE = False
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    
    # Download quietly if missing
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
    
    STOPWORDS_SET = set(stopwords.words('english'))
    STOPWORDS_SET.add('now')  # Add common filler 'now' as stopword
    
    LEMMATIZER = WordNetLemmatizer()
    NLTK_AVAILABLE = True
except Exception:
    STOPWORDS_SET = FALLBACK_STOPWORDS
    LEMMATIZER = None

def fallback_lemmatize(word):
    """
    Lightweight singular/plural lemmatizer fallback.
    Converts plurals back to singular if they end in 'ies' or 's'.
    """
    if len(word) <= 3:
        return word
    if word.endswith("ies") and not word.endswith("eies"):
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith("ss") and not word.endswith("us") and not word.endswith("is"):
        return word[:-1]
    return word

def clean_text(text):
    """
    Full text cleaning pipeline matching user specifications:
    1. Lowercase conversion
    2. URL removal
    3. Emoji/Non-ASCII removal (e.g. ₹, emojis)
    4. Remove punctuation
    5. Number cleaning (removes digits)
    6. Tokenization
    7. Remove stopwords
    8. Lemmatization
    """
    if not isinstance(text, str):
        return ""
    
    # 1. Lowercase conversion
    text_cleaned = text.lower()
    
    # 2. URL removal
    text_cleaned = re.sub(r'https?://\S+|www\.\S+', '', text_cleaned)
    
    # 3. Emoji & Non-ASCII removal
    text_cleaned = re.sub(r'[^\x00-\x7F]+', '', text_cleaned)
    
    # 4. Remove punctuation
    text_cleaned = re.sub(r'[^\w\s]', '', text_cleaned)
    
    # 5. Number cleaning (removes digits)
    text_cleaned = re.sub(r'\d+', '', text_cleaned)
    
    # 6. Tokenization
    if NLTK_AVAILABLE:
        try:
            tokens = word_tokenize(text_cleaned)
        except Exception:
            tokens = text_cleaned.split()
    else:
        tokens = text_cleaned.split()
        
    # 7. Remove stopwords & 8. Lemmatization
    cleaned_tokens = []
    for token in tokens:
        if token not in STOPWORDS_SET and len(token) > 1:
            if NLTK_AVAILABLE and LEMMATIZER:
                try:
                    lemmed = LEMMATIZER.lemmatize(token)
                except Exception:
                    lemmed = fallback_lemmatize(token)
            else:
                lemmed = fallback_lemmatize(token)
            cleaned_tokens.append(lemmed)
            
    return " ".join(cleaned_tokens)

def extract_text_features(raw_text):
    """
    Feature Engineering:
    Creates numeric features from raw text:
    - Message length
    - Number of links
    - Spam keywords count
    - Capital letters count
    """
    if not isinstance(raw_text, str):
        return {
            "length": 0,
            "num_links": 0,
            "spam_keywords_count": 0,
            "capital_letters_count": 0
        }
        
    text_lower = raw_text.lower()
    
    # Message length
    length = len(raw_text)
    
    # Number of links
    num_links = len(re.findall(r'https?://\S+|www\.\S+', raw_text))
    
    # Spam keywords count
    spam_count = 0
    for keyword in SPAM_KEYWORDS:
        spam_count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
        
    # Capital letters count
    cap_count = sum(1 for c in raw_text if c.isupper())
    
    return {
        "length": length,
        "num_links": num_links,
        "spam_keywords_count": spam_count,
        "capital_letters_count": cap_count
    }
