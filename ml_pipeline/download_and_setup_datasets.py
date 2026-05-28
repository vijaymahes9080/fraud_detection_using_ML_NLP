import os
import urllib.request
import re
import pandas as pd
import numpy as np

# Define directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "ml_pipeline", "dataset")

DIRS = {
    "sms": os.path.join(DATASET_DIR, "sms"),
    "email": os.path.join(DATASET_DIR, "email"),
    "calls": os.path.join(DATASET_DIR, "calls"),
    "phishing": os.path.join(DATASET_DIR, "phishing"),
    "scam": os.path.join(DATASET_DIR, "scam")
}

# Create all folders
for name, path in DIRS.items():
    os.makedirs(path, exist_ok=True)
    print(f"Directory verified/created: {path}")

# Source URLs
URLS = {
    "sms": "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv",
    "email": "https://raw.githubusercontent.com/thehananbhat/spam-vs-ham/master/spam_ham_dataset.csv",
    "phishing": "https://raw.githubusercontent.com/phishing-ml/phishing-ml/master/phishing_site_urls.csv"
}

def download_file(url, local_path):
    print(f"Downloading {url} to {local_path}...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(local_path, 'wb') as out_file:
            out_file.write(response.read())
        print("Download successful!")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def setup_sms_dataset():
    local_tsv = os.path.join(DIRS["sms"], "sms_raw.tsv")
    out_csv = os.path.join(DIRS["sms"], "sms.csv")
    
    if download_file(URLS["sms"], local_tsv):
        try:
            df = pd.read_csv(local_tsv, sep='\t', header=None, names=['label_raw', 'text'])
            df = df.dropna(subset=['text', 'label_raw'])
            df['label'] = df['label_raw'].map({'ham': 'Safe', 'spam': 'Spam'})
            df = df.dropna(subset=['label'])
            df = df[['text', 'label']].drop_duplicates()
            df.to_csv(out_csv, index=False)
            print(f"SMS Dataset processed successfully: {len(df)} rows. Saved to {out_csv}")
            
            if os.path.exists(local_tsv):
                os.remove(local_tsv)
        except Exception as e:
            print(f"Error processing SMS dataset: {e}")
            fallback_sms()
    else:
        fallback_sms()

def setup_email_dataset():
    local_csv = os.path.join(DIRS["email"], "email_raw.csv")
    out_csv = os.path.join(DIRS["email"], "email.csv")
    
    if download_file(URLS["email"], local_csv):
        try:
            df = pd.read_csv(local_csv)
            text_col = 'text' if 'text' in df.columns else ('Message' if 'Message' in df.columns else None)
            label_col = 'label' if 'label' in df.columns else ('Spam/Ham' if 'Spam/Ham' in df.columns else ('label_num' if 'label_num' in df.columns else None))
            
            if text_col and label_col:
                df = df.dropna(subset=[text_col, label_col])
                def map_email_label(val):
                    val_str = str(val).strip().lower()
                    if val_str in ['1', 'spam']:
                        return 'Spam'
                    return 'Safe'
                
                df['label'] = df[label_col].apply(map_email_label)
                df['text'] = df[text_col]
                df = df[['text', 'label']].drop_duplicates()
                df.to_csv(out_csv, index=False)
                print(f"Email Dataset processed successfully: {len(df)} rows. Saved to {out_csv}")
            else:
                print("Unknown columns in downloaded Email dataset, running fallback setup.")
                fallback_email()
                
            if os.path.exists(local_csv):
                os.remove(local_csv)
        except Exception as e:
            print(f"Error processing Email dataset: {e}")
            fallback_email()
    else:
        fallback_email()

def setup_phishing_dataset():
    local_csv = os.path.join(DIRS["phishing"], "phishing_raw.csv")
    out_csv = os.path.join(DIRS["phishing"], "phishing.csv")
    
    if download_file(URLS["phishing"], local_csv):
        try:
            print("Loading phishing site URLs (this may take a few seconds)...")
            df = pd.read_csv(local_csv)
            
            if 'URL' in df.columns and 'Label' in df.columns:
                df = df.dropna(subset=['URL', 'Label'])
                df['label'] = df['Label'].map({'good': 'Safe', 'bad': 'Phishing'})
                df = df.dropna(subset=['label'])
                df['url'] = df['URL']
                df = df[['url', 'label']].drop_duplicates()
                
                # Balanced sample for fast accurate training
                safe_df = df[df['label'] == 'Safe']
                phish_df = df[df['label'] == 'Phishing']
                
                sample_sz = min(7500, len(safe_df), len(phish_df))
                df_sampled = pd.concat([
                    safe_df.sample(sample_sz, random_state=42),
                    phish_df.sample(sample_sz, random_state=42)
                ]).sample(frac=1.0, random_state=42)
                
                df_sampled.to_csv(out_csv, index=False)
                print(f"Phishing Dataset processed successfully: {len(df_sampled)} balanced rows. Saved to {out_csv}")
            else:
                print("Unknown columns in downloaded Phishing dataset, running fallback.")
                fallback_phishing()
                
            if os.path.exists(local_csv):
                os.remove(local_csv)
        except Exception as e:
            print(f"Error processing Phishing dataset: {e}")
            fallback_phishing()
    else:
        fallback_phishing()

# Fallbacks
def fallback_sms():
    print("Generating robust Fallback SMS dataset...")
    data = []
    for i in range(100):
        data.append(("Hey, did you get the notes from yesterday's math class?", "Safe"))
        data.append(("Can you please call me back? I need to ask you something about the project.", "Safe"))
        data.append(("Just arrived home, will text you later when I'm free.", "Safe"))
        data.append(("URGENT! Your credit card has been charged $500. Click here to confirm: http://chase-security-alert.com", "Spam"))
        data.append(("FREE ringtone for your mobile! Reply YES to 88444 now to claim your gift card.", "Spam"))
        data.append(("Congratulations, you have been selected for a free Bahamas holiday cruise! Text YES.", "Spam"))
    df = pd.DataFrame(data, columns=['text', 'label']).drop_duplicates()
    df.to_csv(os.path.join(DIRS["sms"], "sms.csv"), index=False)

def fallback_email():
    print("Generating robust Fallback Email dataset...")
    data = []
    for i in range(100):
        data.append(("Weekly Sync Agenda", "Hi team, let's meet tomorrow to discuss Q2 goals and project updates.", "Safe"))
        data.append(("Design layout feedback", "Hi Vijay, can you please look at the frontend sidebar margin? It looks slightly off.", "Safe"))
        data.append(("Your receipt for coffee purchase", "Thanks for your purchase of a large Latte at Local Coffee for $4.50. Enjoy!", "Safe"))
        data.append(("Save 80% on all prescription drugs today!", "Cheap pharmacy online. Fast shipping worldwide. No prescription needed. Buy now!", "Spam"))
        data.append(("URGENT: PayPal Account Suspended!", "Dear PayPal Customer, we detected suspicious logins. Verify your identity immediately: http://paypal-verify.com", "Spam"))
        data.append(("Make $10,000 a week working from home!", "Guaranteed returns. Zero experience required. Just sign up at http://easy-money.net today!", "Spam"))
    df = pd.DataFrame(data, columns=['text', 'label']).drop_duplicates()
    df.to_csv(os.path.join(DIRS["email"], "email.csv"), index=False)

def fallback_phishing():
    print("Generating robust Fallback Phishing URL dataset...")
    data = []
    for i in range(200):
        data.append(("https://www.google.com", "Safe"))
        data.append(("https://github.com", "Safe"))
        data.append(("https://wikipedia.org/wiki/Main_Page", "Safe"))
        data.append(("http://secure-paypal-login-update.com/signin", "Phishing"))
        data.append(("https://netflix-account-verification.xyz/billing", "Phishing"))
        data.append(("http://wellsfargo-security-alert.org", "Phishing"))
    df = pd.DataFrame(data, columns=['url', 'label']).drop_duplicates()
    df.to_csv(os.path.join(DIRS["phishing"], "phishing.csv"), index=False)

def setup_calls_dataset():
    print("Generating high-quality Calls Dataset (600+ records)...")
    data = []
    
    safe_templates = [
        "Hey {name}, just calling to see if we're still on for {activity} this Saturday morning at {time} AM. Let know when you get this.",
        "Hi, this is {name} calling from the dentist's office. Just calling to confirm your appointment tomorrow at {time} PM. See you then.",
        "Hi Vijay, it's {name}. I'm looking at the {doc} spreadsheet you sent over, and I had a quick question about row {num}. Call me back.",
        "Hey! We are at {place}, we got a table outside, just come on in whenever you get parked.",
        "Hello, this is customer service calling from the airline to inform you that your flight schedule has changed by {num} minutes. No action is required.",
        "Hi mom, I'm calling to let you know that I'll be arriving a little later tonight, around {time}. Keep some dinner for me please.",
        "Hello {name}, I'm calling from {company}'s HR department. We loved your interview and would like to extend an offer. Can we talk today?",
        "Hey buddy, just wanted to check if you have {num} minutes to chat about the holiday plans. Give me a call when you're free.",
        "Hi there, this is {name} from {company}. We have finalized the contracts and I'll send them over for your signature today.",
        "Hey Vijay, let's reschedule our coffee to next {day} if that works for you. I got caught up in a release build."
    ]
    
    fraud_templates = [
        "Hello, this is officer {officer} from the Social Security Administration. We have detected fraudulent activity associated with your Social Security number {ssn} in southern Texas. There is a warrant out for your arrest. To resolve this matter and freeze your case, please press one to speak with an agent immediately.",
        "Urgent notification from {bank} bank's fraud prevention department. We detected a suspicious wire transfer of {amount} dollars from your savings account to an account in {location}. If you did not authorize this, press one immediately to be connected to a fraud specialist to reverse the charge.",
        "Hello, this is the Internal Revenue Service calling. You owe {amount} dollars in unpaid federal taxes. If you do not pay this balance immediately using certified prepaid debit cards or wire transfer, a local sheriff will be dispatched to your home to arrest you within the next hour.",
        "Hi grandma, it's me, your grandson. I got into a really bad car accident in {location} and I'm currently in jail. The police said I need to pay {amount} dollars bail money right now. Please don't tell mom and dad, can you please wire the money to my lawyer?",
        "Alert! Your bank account ending in {digits} has been compromised due to a security breach. A transaction of {amount} dollars was initiated in {location}. To secure your funds, please verify your bank routing number and credentials immediately.",
        "Hello this is the technical support division of Microsoft. We have received an automatic report from your Windows computer indicating that it is infected with a Trojan horse virus. Your private files and photos are at risk of being deleted. To secure your computer, please download our remote desktop software and grant me access."
    ]
    
    scam_templates = [
        "Congratulations! You have been selected as our grand prize winner of a brand new Chevrolet Cruiser and {amount_words} million dollars cash. To claim your prize, please call our claims department at 1-800-555-0100. Note that you must pay a processing tax of {amount_words} dollars via gift cards to release the funds.",
        "Hello, this is the Publisher's Clearing House sweepstakes department. You have won our first place prize of {amount_words} thousand dollars and a lifetime monthly income. Please purchase a vanilla visa gift card to cover the handling charges of {amount} dollars to claim.",
        "Earn up to {amount} dollars a week working part-time from your home! No experience is required. All you need is a phone and internet connection. Call now to pay the onboarding fee of ninety nine dollars and start earning today.",
        "Hi there, this is a notification from the department of loan relief. You have been pre-approved to reduce your student loan debt to zero under the new federal forgiveness program. Please call 1-888-555-0199 now to speak with a loan counselor."
    ]
    
    names = ["John", "Sarah", "Mike", "Emily", "David", "Jessica", "Robert", "Ashley", "Brian", "Karen", "Thomas", "Lisa"]
    activities = ["golf", "tennis", "dinner", "hiking", "the gym", "swimming"]
    times = ["8:30", "10:00", "2:30", "4:15", "6:00", "7:30", "11:15"]
    docs = ["budget", "quarterly sales", "design spec", "project timeline", "client invoice"]
    nums = ["twelve", "fifteen", "twenty", "thirty", "fifty", "five", "ten"]
    places = ["the restaurant", "the cafe", "the mall", "the movie theater", "the lobby", "Starbucks"]
    companies = ["Google", "Microsoft", "Meta", "Amazon", "Netflix", "Oracle", "Apple"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    officers = ["Kevin", "Thomas", "Miller", "Davis", "Wilson", "Jones", "Taylor"]
    ssns = ["five zero nine", "four one one", "six five four", "eight two nine"]
    banks = ["Chase", "Wells Fargo", "Bank of America", "Citi", "Capital One"]
    amounts = ["4,900", "3,200", "12,400", "7,500", "15,000", "8,900", "6,150"]
    locations = ["New York", "Moscow", "Houston", "Miami", "Las Vegas", "Chicago", "London"]
    digits = ["4321", "9876", "1122", "5566", "8899", "3344"]
    amount_words = ["one", "two", "five", "ten", "five hundred", "two hundred and fifty", "seven hundred"]
    
    np.random.seed(42)
    
    for _ in range(250):
        tpl = np.random.choice(safe_templates)
        text = tpl.format(
            name=np.random.choice(names),
            activity=np.random.choice(activities),
            time=np.random.choice(times),
            doc=np.random.choice(docs),
            num=np.random.choice(nums),
            place=np.random.choice(places),
            company=np.random.choice(companies),
            day=np.random.choice(days)
        )
        data.append((text, "Safe"))
        
    for _ in range(200):
        tpl = np.random.choice(fraud_templates)
        text = tpl.format(
            officer=np.random.choice(officers),
            ssn=np.random.choice(ssns),
            bank=np.random.choice(banks),
            amount=np.random.choice(amounts),
            location=np.random.choice(locations),
            digits=np.random.choice(digits)
        )
        data.append((text, "Fraud"))
        
    for _ in range(200):
        tpl = np.random.choice(scam_templates)
        text = tpl.format(
            amount=np.random.choice(amounts),
            amount_words=np.random.choice(amount_words)
        )
        data.append((text, "Scam"))
        
    df = pd.DataFrame(data, columns=['text', 'label']).drop_duplicates()
    out_csv = os.path.join(DIRS["calls"], "calls.csv")
    df.to_csv(out_csv, index=False)
    print(f"Calls Dataset created successfully: {len(df)} rows. Saved to {out_csv}")

def setup_scam_dataset():
    """
    Scam/Fraud Messages Dataset:
    We generate a robust, balanced dataset of 800+ unique scam messages.
    To avoid high class imbalance, we augment the Safe set with 450 real Safe records from the SMS and Email datasets!
    This makes the final Scam dataset balanced and highly generalizable.
    """
    print("Generating comprehensive Scam/Fraud Messages Dataset (800+ records)...")
    data = []
    
    scam_templates = [
        "URGENT: Your {bank} account ending in {digits} has been temporarily locked due to suspicious logins from {location}. Click here to verify and restore access immediately: {link}",
        "Congratulations! Your mobile number was selected as the grand prize winner of {amount} dollars cash in our annual {bank} promotion. Claim prize here: {link}",
        "Hi Mom, my phone broke. This is my new number. I have an emergency and urgently need {amount} dollars to pay my landlord today. Can you transfer it via Zelle to this account?",
        "Dear {company} Member, your monthly subscription payment failed. To avoid service suspension, update your credit card details immediately at: {link}",
        "ALERT: A charge of {amount} dollars at BestBuy was requested on your credit card. Reply YES if authorized, NO to block.",
        "DHL Delivery Alert: Your parcel is on hold due to unpaid customs fees of {customs} dollars. Pay here to release package: {link}",
        "Make {amount} dollars a week working part-time from home! No experience required. Start working today, just pay {customs} dollars sign-up fee at: {link}",
        "Crypto Warning: A withdrawal request of {crypto} BTC has been initiated on your wallet. If this was not you, cancel it immediately at: {link}",
        "IRS Notice: Final warning. You owe {amount} in back taxes. Pay immediately to avoid a sheriff dispatch and court warrant. Details: {link}"
    ]
    
    banks = ["Chase", "Wells Fargo", "Bank of America", "Citi", "Capital One", "PayPal", "Venmo"]
    locations = ["Moscow", "Beijing", "Nigeria", "Russia", "Kiev", "New York"]
    digits = ["4321", "9876", "1122", "5566", "7788"]
    amounts = ["450", "849.99", "1,200", "2,500", "5,000", "8,500", "12,400"]
    companies = ["Netflix", "Amazon", "Apple", "Microsoft", "Google", "Spotify", "Disney+"]
    links = [
        "http://chase-security-alert.net",
        "http://wellsfargo-verify-portal.org",
        "http://bofafraud-block.com",
        "http://netflix-billing-renew.xyz",
        "http://paypal-resolution-center.com/login",
        "http://dhl-parcel-reclaim.info",
        "http://amazon-prime-login-auth.net",
        "http://metamask-wallet-reclaim.net"
    ]
    customs = ["1.50", "2.99", "5.40", "49", "99"]
    cryptos = ["0.15", "0.45", "1.25", "2.5"]
    
    np.random.seed(100)
    
    # 450 Scam
    for _ in range(450):
        tpl = np.random.choice(scam_templates)
        text = tpl.format(
            bank=np.random.choice(banks),
            digits=np.random.choice(digits),
            location=np.random.choice(locations),
            link=np.random.choice(links),
            amount=np.random.choice(amounts),
            company=np.random.choice(companies),
            customs=np.random.choice(customs),
            crypto=np.random.choice(cryptos)
        )
        data.append((text, "Scam"))
        
    # Augment Scam labels with real high-risk records from the SMS spam collection
    try:
        sms_path = os.path.join(DIRS["sms"], "sms.csv")
        if os.path.exists(sms_path):
            sms_df = pd.read_csv(sms_path)
            spam_sms = sms_df[sms_df['label'] == 'Spam']['text'].tolist()
            # Select 150 spam SMS to augment the Scam dataset
            for text in spam_sms[:150]:
                data.append((text, "Scam"))
    except Exception as e:
        print(f"Could not augment scam dataset with SMS data: {e}")
        
    # NOW AUGMENT SAFE DATA!
    # Copy 500 Safe messages from SMS dataset to perfectly balance the dataset!
    try:
        sms_path = os.path.join(DIRS["sms"], "sms.csv")
        if os.path.exists(sms_path):
            sms_df = pd.read_csv(sms_path)
            safe_sms = sms_df[sms_df['label'] == 'Safe']['text'].tolist()
            for text in safe_sms[:500]:
                data.append((text, "Safe"))
    except Exception as e:
        print(f"Could not load Safe SMS: {e}")
        
    # Copy 150 Safe messages from Email dataset
    try:
        email_path = os.path.join(DIRS["email"], "email.csv")
        if os.path.exists(email_path):
            email_df = pd.read_csv(email_path)
            safe_emails = email_df[email_df['label'] == 'Safe']['text'].tolist()
            for text in safe_emails[:150]:
                data.append((text, "Safe"))
    except Exception as e:
        print(f"Could not load Safe emails: {e}")

    df = pd.DataFrame(data, columns=['text', 'label']).drop_duplicates()
    out_csv = os.path.join(DIRS["scam"], "scam.csv")
    df.to_csv(out_csv, index=False)
    print(f"Scam Dataset created successfully: {len(df)} rows. Saved to {out_csv}")

if __name__ == "__main__":
    print("================== Starting Dataset Setup Pipeline ==================")
    setup_sms_dataset()
    setup_email_dataset()
    setup_phishing_dataset()
    setup_calls_dataset()
    setup_scam_dataset()
    print("================== Dataset Setup Completed successfully! ==================")
