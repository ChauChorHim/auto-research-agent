import json
import logging
import os
from httplib2 import Http
from auto_research_agent.src.schemas import WeeklyResearchDigest

logger = logging.getLogger(__name__)

def send_to_google_chat(digest_data: WeeklyResearchDigest):
    """Sends the digest data to Google Chat via Webhook."""
    webhook_url = os.environ.get("GOOGLE_CHAT_WEBHOOK_URL") or os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        logger.warning("GOOGLE_CHAT_WEBHOOK_URL (or WEBHOOK_URL) not found. Skipping Google Chat notification.")
        return

    # Construct the message
    header = f"*{digest_data.topic} - {digest_data.report_date}*\n\n"
    
    items_text = ""
    for i, item in enumerate(digest_data.items, 1):
        items_text += f"*{i}. {item.title}*\n"
        items_text += f"<{item.source_link}|Source> | `Domain: {item.primary_domain.value}`\n"
        items_text += f"> {item.key_innovation}\n\n"

    message_text = header + items_text

    # Basic text message with formatting
    app_message = {"text": message_text}
    
    message_headers = {"Content-Type": "application/json; charset=UTF-8"}
    
    try:
        http_obj = Http()
        response, content = http_obj.request(
            uri=webhook_url,
            method="POST",
            headers=message_headers,
            body=json.dumps(app_message),
        )
        logger.info(f"Google Chat response: {response.status}")
    except Exception as e:
        logger.error(f"Failed to send to Google Chat: {e}")
