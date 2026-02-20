import os
import feedparser
import requests
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
# These will be pulled from GitHub Secrets automatically
WP_POST_EMAIL = os.getenv('WP_POST_EMAIL')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')

# Model Configuration
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

# RSS Feeds (Corrected with .rss and commas)
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
    # Add User-Agent to avoid being blocked by Reddit
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; AutoBlogBot/1.0)'}
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url, agent=headers)
            for entry in feed.entries[:2]:  # Limit to 2 per source to save tokens
                all_entries.append(f"- {entry.title}: {entry.summary}")
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
    
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
        # Removed spaces in URL
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 503:
            return "Error: Model is loading. Please try again later."
            
        result = response.json()
        # Handle different response structures
        if isinstance(result, list):
            return result[0]['generated_text']
        else:
            return result['generated_text']
            
    except Exception as e:
        return f"Error generating content: {e}"

def send_email_to_wordpress(subject, body):
    """Sends an email to the WordPress Post-by-Email address."""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = WP_POST_EMAIL
    msg['Subject'] = subject
    
    # WordPress publishes the email body as the post content
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(GMAIL_USER, WP_POST_EMAIL, text)
        server.quit()
        print("Email sent successfully! Post should appear on blog.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Fetching news...")
    news = fetch_news()
    
    if news:
        print("Generating summary...")
        article = generate_summary(news)
        
        if "Error" in article:
            print(article)
        else:
            # Split title and body
            lines = article.split('\n', 1)
            title = lines[0].replace("#", "").strip()
            body = lines[1] if len(lines) > 1 else article
            
            print(f"Sending post titled: {title}")
            send_email_to_wordpress(title, body)
    else:
        print("No news found to summarize.")
