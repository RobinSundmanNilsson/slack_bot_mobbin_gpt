import os
import time
import threading
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
import google.generativeai as genai

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print("DEBUG SLACK_BOT_TOKEN:", bool(SLACK_BOT_TOKEN))
print("DEBUG SLACK_APP_TOKEN:", bool(SLACK_APP_TOKEN))
print("DEBUG GEMINI_API_KEY:", bool(GEMINI_API_KEY))
if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Missing one or more required environment variables.")

app = App(token=SLACK_BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# simple in-memory storage for message history
message_history = {}
last_response = {}
cooldown_threads = {}

# config
WINDOW_SECONDS = 120  # time window to consider past messages
THRESHOLD_MESSAGES = 3  # number of messages to trigger response
COOLDOWN_SECONDS = 120  # cooldown period after a response
MAX_CONTEXT_MESSAGES = 10  # max number of past messages to include in context


# helper functions:
# clean up old messages from history
def prune_history(channel_id, now_ts):
    """Prune messages older than WINDOW_SECONDS from history."""
    global message_history
    timestamps = message_history.get(channel_id, [])
    message_history[channel_id] = [
        ts for ts in timestamps if now_ts - ts < WINDOW_SECONDS
    ]


# build prompt for Gemini
def build_prompt_text(messages):
    """Transform Slack history into a prompt for Gemini."""
    # sorting: older -> newer
    sorted_messages = sorted(messages, key=lambda m: float(m["ts"]))
    lines = []
    for msg in sorted_messages:
        user = msg.get("user", "unknown")
        text = msg.get("text", "")
        lines.append(f"{user}: {text}")
    return "\n".join(lines)


# generate response from Gemini
def generate_response(context_text: str) -> str:
    """Generate a roast/unhinged style response using Gemini."""
    system_prompt = (
        "Du är en extremt roastig och kaotisk bot i en privat vänkanal. "
        "Du får vara aggressivt skämtsam, sarkastisk och överdriven, men du MÅSTE följa detta:\n"
        "- Inga rasistiska, sexistiska, homofoba eller andra hatfulla uttryck.\n"
        "- Ingen politik, religion eller riktiga trauman.\n"
        "- Inga hot eller uppmaningar till våld.\n"
        "- Max 50 ord i svaret.\n"
        "Skriv på svenska och låt det tydligt vara humor mellan vänner."
    )

    prompt = (
        f"{system_prompt}\n\n"
        "Här är de senaste meddelandena i kanalen:\n\n"
        f"{context_text}\n\n"
        "Svara med EN kort, roastig och kaotisk replik. Ingen förklaring, bara själva meddelandet."
    )

    try:
        response = gemini_model.generate_content(prompt)
        text = response.text or ""
        return text.strip()
    
    except Exception as e:
        return f"(Gemini error) {str(e)}"

# slack event handler
def start_cooldown_timer(channel: str, duration: int):
    """Log a simple countdown in the terminal without blocking the main loop."""
    # stop any existing timer for this channel
    existing = cooldown_threads.get(channel)
    if existing:
        existing["stop"].set()

    stop_event = threading.Event()

    def _run():
        for remaining in range(duration, 0, -1):
            if stop_event.is_set():
                return
            print(f"DEBUG COOLDOWN: {channel} {remaining}s left")
            time.sleep(1)
        if not stop_event.is_set():
            print(f"DEBUG COOLDOWN: {channel} ready")

    t = threading.Thread(target=_run, daemon=True)
    cooldown_threads[channel] = {"stop": stop_event, "thread": t}
    t.start()


@app.event("message")
def handle_message_events(body, event, say, client, logger):
    try:
        print("DEBUG EVENT:", event)
        # ignore messages from bots
        if event.get("subtype") == "bot_message":
            print("DEBUG SKIP: bot_message subtype")
            return
        
        channel = event.get("channel")
        if not channel:
            print("DEBUG SKIP: missing channel id")
            return
        
        now_ts = time.time()

        # update message history
        message_history.setdefault(channel, []).append(now_ts)
        prune_history(channel, now_ts)

        # cooldown control
        last_ts = last_response.get(channel, 0)
        if now_ts - last_ts < COOLDOWN_SECONDS:
            elapsed = int(now_ts - last_ts)
            remaining = max(0, COOLDOWN_SECONDS - elapsed)
            print(
                f"DEBUG SKIP: cooldown active "
                f"({elapsed}s since last reply, {remaining}s remaining)"
            )
            return
        
        # threshold control
        if len(message_history[channel]) < THRESHOLD_MESSAGES:
            print(
                f"DEBUG SKIP: threshold not met "
                f"({len(message_history[channel])}/{THRESHOLD_MESSAGES} messages in window)"
            )
            return
        
        # fetch recent messages for context
        print("DEBUG ACTION: fetching conversation history")
        history = client.conversations_history(
            channel=channel,
            limit=MAX_CONTEXT_MESSAGES,
        )
        messages = history.get("messages", [])
        if not messages:
            print("DEBUG SKIP: no messages returned")
            return
        
        context_text = build_prompt_text(messages)

        # generate response
        print("DEBUG ACTION: composing message with Gemini")
        reply = generate_response(context_text)

        # send reply
        print("DEBUG ACTION: sending reply to Slack")
        say(text=reply)

        # update last response time
        last_response[channel] = now_ts
        start_cooldown_timer(channel, COOLDOWN_SECONDS)

    except SlackApiError as e:
        logger.error(f"Slack API Error: {e.response['error']}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
