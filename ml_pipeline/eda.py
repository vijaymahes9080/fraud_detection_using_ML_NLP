import os
import re
import collections
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set plotting styles for premium cyber-security visual aesthetics
sns.set_theme(style="darkgrid")
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16,
    'figure.facecolor': '#1E1E2E',  # Premium dark background
    'axes.facecolor': '#252538',
    'axes.edgecolor': '#44445c',
    'text.color': '#F8F8F2',
    'axes.labelcolor': '#F8F8F2',
    'xtick.color': '#F8F8F2',
    'ytick.color': '#F8F8F2',
})

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "ml_pipeline", "dataset")
VIS_DIR = os.path.join(BASE_DIR, "ml_pipeline", "eda_visualizations")
os.makedirs(VIS_DIR, exist_ok=True)

# Load helper NLP processor to extract clean words
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml_pipeline.nlp_preprocessor import clean_text, extract_text_features

def load_all_datasets():
    datasets = {}
    
    # SMS
    sms_path = os.path.join(DATASET_DIR, "sms", "sms.csv")
    if os.path.exists(sms_path):
        datasets["SMS"] = pd.read_csv(sms_path)
        
    # Email
    email_path = os.path.join(DATASET_DIR, "email", "email.csv")
    if os.path.exists(email_path):
        datasets["Email"] = pd.read_csv(email_path)
        
    # Calls
    calls_path = os.path.join(DATASET_DIR, "calls", "calls.csv")
    if os.path.exists(calls_path):
        datasets["Calls"] = pd.read_csv(calls_path)
        
    # Phishing
    phishing_path = os.path.join(DATASET_DIR, "phishing", "phishing.csv")
    if os.path.exists(phishing_path):
        datasets["Phishing"] = pd.read_csv(phishing_path)
        
    # Scam
    scam_path = os.path.join(DATASET_DIR, "scam", "scam.csv")
    if os.path.exists(scam_path):
        datasets["Scam"] = pd.read_csv(scam_path)
        
    return datasets

def plot_spam_vs_ham_distribution(datasets):
    print("Generating distribution counts plot...")
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()
    
    colors = {"Safe": "#4E9F3D", "Spam": "#D83A56", "Phishing": "#FF6B6B", "Fraud": "#D32F2F", "Scam": "#E64A19"}
    
    for idx, (name, df) in enumerate(datasets.items()):
        ax = axes[idx]
        counts = df['label'].value_counts()
        
        # Select colors based on classes present
        palette = [colors.get(c, "#888888") for c in counts.index]
        
        sns.barplot(x=counts.index, y=counts.values, ax=ax, palette=palette)
        ax.set_title(f"{name} Category Distribution", pad=10, weight='bold')
        ax.set_ylabel("Count")
        ax.set_xlabel("Class")
        
        # Display percentages above bars
        total = sum(counts.values)
        for p in ax.patches:
            height = p.get_height()
            percentage = f"{100 * height / total:.1f}%"
            ax.annotate(percentage,
                        xy=(p.get_x() + p.get_width() / 2, height),
                        xytext=(0, 5),  # 5 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, color='#F8F8F2')
            
    # Hide the 6th empty axes
    if len(datasets) < 6:
        axes[5].axis('off')
        
    plt.suptitle("Spam vs Ham / Threat Ratios Across Datasets", weight='bold', y=0.98)
    plt.tight_layout()
    out_path = os.path.join(VIS_DIR, "spam_vs_ham_distribution.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Saved: {out_path}")

def plot_most_common_spam_words(datasets):
    print("Generating most common spam words plot...")
    spam_words = []
    
    # Aggregate words from SMS (Spam), Email (Spam), Call (Fraud/Scam), Scam (Scam)
    for name, df in datasets.items():
        if 'text' not in df.columns:
            continue
            
        threat_df = df[df['label'].isin(['Spam', 'Scam', 'Fraud'])]
        for text in threat_df['text'].dropna():
            cleaned = clean_text(text)
            spam_words.extend(cleaned.split())
            
    counter = collections.Counter(spam_words)
    common = counter.most_common(15)
    
    words = [x[0] for x in common]
    counts = [x[1] for x in common]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=counts, y=words, ax=ax, palette="Oranges_r")
    
    ax.set_title("Top 15 Most Frequent Words in Spam & Scam Messages", pad=15, weight='bold')
    ax.set_xlabel("Frequency Count")
    ax.set_ylabel("Cleaned Words")
    
    plt.tight_layout()
    out_path = os.path.join(VIS_DIR, "most_common_spam_words.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Saved: {out_path}")

def generate_pseudo_wordcloud(datasets):
    """
    Generates a stunning, stylized Word Cloud layout inside a Matplotlib frame.
    Avoids compilation and package errors from C-based wordcloud module.
    """
    print("Generating stylized Word Cloud...")
    all_words = []
    
    for name, df in datasets.items():
        if 'text' not in df.columns:
            continue
        threat_df = df[df['label'].isin(['Spam', 'Scam', 'Fraud'])]
        for text in threat_df['text'].dropna():
            all_words.extend(clean_text(text).split())
            
    counter = collections.Counter(all_words)
    top_words = counter.most_common(50)
    
    if not top_words:
        print("No words available for word cloud.")
        return
        
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='#1E1E2E')
    ax.set_facecolor('#1E1E2E')
    
    # Hide axis borders
    ax.axis('off')
    
    # Max/Min bounds for positioning
    np.random.seed(42)
    
    # Colors for threat aesthetics: glows, reds, oranges, ambers
    word_colors = ['#FF4C29', '#FFD369', '#FF8A08', '#D83A56', '#FF9F45', '#FF6B6B', '#FF8E8E', '#FFB3B3']
    
    # Spiral placement algorithm
    # To place words elegantly in a central cluster
    for idx, (word, count) in enumerate(top_words):
        # Determine relative size
        max_cnt = top_words[0][1]
        min_cnt = top_words[-1][1]
        
        # Map count linearly to font sizes [12, 48]
        if max_cnt == min_cnt:
            fs = 20
        else:
            fs = int(12 + 36 * (count - min_cnt) / (max_cnt - min_cnt))
            
        # Compute coordinate along an Archimedean spiral: r = a + b * theta
        theta = idx * 0.45
        r = 1.8 * np.sqrt(idx)
        
        x = r * np.cos(theta) + np.random.uniform(-0.3, 0.3)
        y = r * np.sin(theta) + np.random.uniform(-0.3, 0.3)
        
        color = np.random.choice(word_colors)
        
        # Plot word with nice cybersecurity styling
        ax.text(x, y, word, fontsize=fs, color=color, ha='center', va='center',
                weight='bold', alpha=0.9,
                bbox=dict(facecolor='#252538', alpha=0.3, edgecolor='none', boxstyle='round,pad=0.2'))
        
    ax.set_xlim(-15, 15)
    ax.set_ylim(-15, 15)
    
    plt.suptitle("Spam & Scam Word Cloud (Term Frequencies)", weight='bold', color='#F8F8F2', y=0.95)
    plt.tight_layout()
    out_path = os.path.join(VIS_DIR, "word_frequency_cloud.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Saved: {out_path}")

def plot_message_length_distribution(datasets):
    print("Generating message length analysis plot...")
    lengths_data = []
    
    for name, df in datasets.items():
        if 'text' not in df.columns:
            continue
            
        for idx, row in df.dropna(subset=['text', 'label']).iterrows():
            text = row['text']
            label = row['label']
            
            # Map classes to binary Safe vs Threat for clear density overview
            category = "Safe" if label == "Safe" else "Threat (Spam/Scam/Fraud)"
            lengths_data.append({"Length": len(text), "Category": category, "Dataset": name})
            
    lengths_df = pd.DataFrame(lengths_data)
    
    # Filter extreme outliers for clear visualization (> 1000 characters)
    lengths_df_filtered = lengths_df[lengths_df['Length'] <= 1000]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Density plot
    sns.kdeplot(data=lengths_df_filtered, x="Length", hue="Category", fill=True, common_norm=False, 
                palette={"Safe": "#4E9F3D", "Threat (Spam/Scam/Fraud)": "#D83A56"}, alpha=0.4, linewidth=2, ax=ax)
                
    ax.set_title("Message Length Density Distribution (Truncated at 1,000 Chars)", pad=15, weight='bold')
    ax.set_xlabel("Message Character Length")
    ax.set_ylabel("Density")
    
    plt.tight_layout()
    out_path = os.path.join(VIS_DIR, "message_length_distribution.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Saved: {out_path}")

def plot_link_frequency(datasets):
    print("Generating link frequency analysis plot...")
    link_data = []
    
    for name, df in datasets.items():
        # Text datasets
        if 'text' in df.columns:
            for idx, row in df.dropna(subset=['text', 'label']).iterrows():
                text = row['text']
                label = row['label']
                category = "Safe" if label == "Safe" else "Threat"
                
                # Check for links in text
                has_link = 1 if re.search(r'https?://\S+|www\.\S+', text.lower()) else 0
                link_data.append({"Category": category, "Has Link": has_link, "Dataset": name})
                
        # URL dataset is 100% links, so we skip it to prevent extreme skew
        
    link_df = pd.DataFrame(link_data)
    
    # Compute link ratios
    ratios = link_df.groupby("Category")["Has Link"].mean().reset_index()
    ratios["Percentage"] = ratios["Has Link"] * 100
    
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(data=ratios, x="Category", y="Percentage", palette={"Safe": "#4E9F3D", "Threat": "#D83A56"}, ax=ax)
    
    ax.set_title("Link Presence Ratios in Safe vs Threat Messages", pad=15, weight='bold')
    ax.set_ylabel("Percentage containing Links (%)")
    ax.set_xlabel("Message Category")
    
    # Display values above bars
    for p in ax.patches:
        height = p.get_height()
        ax.annotate(f"{height:.2f}%",
                    xy=(p.get_x() + p.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom', weight='bold')
                    
    plt.tight_layout()
    out_path = os.path.join(VIS_DIR, "link_frequency_analysis.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    print("================== Starting Exploratory Data Analysis ==================")
    datasets = load_all_datasets()
    if not datasets:
        print("No datasets loaded. Exiting.")
        sys.exit(1)
        
    print(f"Loaded {len(datasets)} datasets: {list(datasets.keys())}")
    
    plot_spam_vs_ham_distribution(datasets)
    plot_most_common_spam_words(datasets)
    generate_pseudo_wordcloud(datasets)
    plot_message_length_distribution(datasets)
    plot_link_frequency(datasets)
    
    print("================== Exploratory Data Analysis Completed! All plots saved in ml_pipeline/eda_visualizations/ ==================")
