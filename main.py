from app import app
from google_services import sheets_service
import time

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
# Add to main.py
def filter_urgent_messages(messages):
    if not messages:  # Handle empty input
        return [{"text": "No urgent messages found.", "priority": "N/A"}]
    return [msg for msg in messages if "urgent" in msg["text"].lower()]

# Example usage
messages = [
    {"text": "Urgent: Staff meeting", "priority": "High"},
    {"text": "Routine check", "priority": "Low"}
]
urgent_messages = filter_urgent_messages(messages)

for msg in urgent_messages:
    try:
        sheets_service.log_message("System", msg["text"], "filter_urgent", msg["priority"])
    except gspread.exceptions.APIError as e:
        print(f"API error: {e}")
        time.sleep(60)  # Wait for rate limit