import os
import feedparser
import requests
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
WP_POST_EMAIL = os.getenv('WP_POST_EMAIL')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Gemini Model (Stable & Free)
GEMINI_MODEL = "gemini-2.0-flash-exp"

# RSS Feeds
RSS_FEEDS = [
    "https://www.reddit.com/r/GeminiAI/top/.rss?limit=5&t=week",
    "https://www.reddit.com/r/OpenAI/top/.rss?limit=5&t=week",
    "https://www.reddit.com/r/ClaudeAI/top/.rss?limit=5&t=week",
    "https://www.reddit.com/r/DeepSeek/top/.rss?limit=5&t=week",
    "https://www.reddit.com/r/Qwen_AI/top/.rss?limit=5&t=week",
    "https://techcrunch.com/feed/"
]

# --- FUNCTIONS ---

def fetch_news():
    """Fetches latest entries from RSS feeds."""
    all_entries = []
    
    for feed_url in RSS_FEEDS:
        try:
            clean_url = feed_url.strip()
            feed = feedparser.parse(clean_url, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            if feed.entries:
                for entry in feed.entries[:2]:
                    title = entry.title if entry.title else "No Title"
                    summary = entry.summary if entry.summary else "No Summary"
                    all_entries.append(f"- {title}: {summary[:200]}...")
                print(f"✓ Successfully fetched: {clean_url[:50]}...")
            else:
                print(f"⚠ No entries found: {clean_url[:50]}...")
                
        except Exception as e:
            print(f"✗ Error fetching {clean_url[:50]}...: {str(e)}")
    
    if not all_entries:
        return None
    return "\n".join(all_entries)

def generate_summary(news_text):
    """Sends text to Google Gemini API for summarization."""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"""You are an expert editor for a niche AI blog. 
Summarize the following news items into a coherent, engaging 500-word article.

FORMAT REQUIREMENTS:
1. The first line must be the Title only (no markdown, no # symbols).
2. The rest of the text is the body content.
3. Include an Affiliate Disclosure at the very bottom.
4. Write in a professional, engaging tone.

News Items:
{news_text}"""
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000,
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: Gemini API returned status {response.status_code} - {response.text[:200]}"
            
    except Exception as e:
        return f"Error generating content: {str(e)}"

def send_email_to_wordpress(subject, body):
    """Sends an email to the WordPress Post-by-Email address."""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = WP_POST_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(GMAIL_USER, WP_POST_EMAIL, text)
        server.quit()
        print("✓ Email sent successfully! Post should appear on blog.")
    except Exception as e:
        print(f"✗ Failed to send email: {str(e)}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("=" * 50)
    print("Starting Auto Blog Bot (Gemini Edition)...")
    print("=" * 50)
    
    print("\n[1/3] Fetching news...")
    news = fetch_news()
    
    if news:
        print(f"\n[2/3] Generating summary via Google Gemini...")
        article = generate_summary(news)
        
        if "Error" in article:
            print(f"\n✗ {article}")
        else:
            lines = article.split('\n', 1)
            title = lines[0].replace("#", "").strip()
            body = lines[1] if len(lines) > 1 else article
            
            print(f"\n[3/3] Sending post titled: {title}")
            send_email_to_wordpress(title, body)
    else:
        print("\n✗ No news found to summarize.")
    
    print("\n" + "=" * 50)
    print("Bot execution complete.")
    print("=" * 50)
