import os
import feedparser
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
WP_POST_EMAIL = os.getenv('WP_POST_EMAIL')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')

HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

# RSS Feeds - NO TRAILING SPACES, NO EXTRA CHARACTERS
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
            # Strip any whitespace from URL
            clean_url = feed_url.strip()
            
            # Add User-Agent to avoid being blocked
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
    """Sends text to Hugging Face Inference API for summarization."""
    prompt = f"""
    You are an expert editor for a niche AI blog. 
    Summarize the following news items into a coherent, engaging 500-word article.
    
    FORMAT REQUIREMENTS:
    1. The first line must be the Title only.
    2. The rest of the text is the body.
    3. Include an Affiliate Disclosure at the very bottom.
    4. Do not use Markdown headers (###) for the title, just plain text.
    
    News Items:
    {news_text}
    """
    
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 600, "temperature": 0.7, "return_full_text": False}
    }
    
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 503:
            return "Error: Model is loading. Please try again later."
        
        if response.status_code != 200:
            return f"Error: API returned status {response.status_code}"
            
        result = response.json()
        if isinstance(result, list):
            return result[0]['generated_text']
        else:
            return result['generated_text']
            
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
    print("Starting Auto Blog Bot...")
    print("=" * 50)
    
    print("\n[1/3] Fetching news...")
    news = fetch_news()
    
    if news:
        print(f"\n[2/3] Generating summary...")
        print(f"Found {len(news.split(chr(10)))} news items")
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
        print("Tip: Check if RSS feeds are accessible or try alternative sources.")
    
    print("\n" + "=" * 50)
    print("Bot execution complete.")
    print("=" * 50)
