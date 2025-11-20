# 🤖 MobbinGPT - A Chaotic Roast Bot for Slack (Powered by Gemini)

MobbinGPT is a chaotic, roast-style Slack bot built with **Python**,
**Slack Bolt (Socket Mode)**, and **Google Gemini**.\

It listens to activity inside a Slack channel and, when users send a burst of messages, the bot generates a short, unhinged, humorous roast based on the recent conversation.

Perfect for private friend groups who enjoy roasting each other for sport. 🔥

------------------------------------------------------------------------

## 🚀 Features

-   Monitors real-time Slack channel activity
-   Detects message bursts (e.g., 4 messages within 60 seconds)
-   Fetches recent Slack conversation history
-   Uses **Gemini 2.5 Flash** to generate a short chaotic roast
-   Cooldown system to prevent spam
-   Safe roast rules (no hate, threats, or sensitive topics)
-   Fully works in **private Slack channels**

------------------------------------------------------------------------

## 🧱 Tech Stack

-   Python 3
-   Slack Bolt (Socket Mode)
-   google-generativeai (Gemini API)
-   Environment variables via `.env`
-   In-memory message tracking

------------------------------------------------------------------------

## 📦 Installation

Clone the repo:

``` bash
git clone <repo-url>
cd slack_bot_mobbin_gpt
```

Install dependencies using **uv**:

``` bash
uv sync
```

------------------------------------------------------------------------

## 🔐 Environment Variables

Create a `.env` file:

    SLACK_BOT_TOKEN=xoxb-...
    SLACK_APP_TOKEN=xapp-...
    GEMINI_API_KEY=...

------------------------------------------------------------------------

## 🧠 Configuration

Inside `bot.py`, you can tweak:

``` python
WINDOW_SECONDS = 120
THRESHOLD_MESSAGES = 3
COOLDOWN_SECONDS = 120
MAX_CONTEXT_MESSAGES = 10
```

**WINDOW_SECONDS**
How far back the bot looks when counting messages.
Example: 120 = count messages from the last 2 minutes.

**THRESHOLD_MESSAGES**
How many messages must appear within the window to trigger a roast.
Example: 3 = any 3 messages within 120 seconds activates the bot.

**COOLDOWN_SECONDS**
Minimum time between bot replies in the same channel.
Example: 120 = bot can only reply once every 2 minutes.

**MAX_CONTEXT_MESSAGES**
How many recent messages are sent to Gemini as context.
Example: 10 = the bot uses the latest 10 messages to craft a roast.

------------------------------------------------------------------------

## ▶️ Running the Bot

Activate the virtual environment:

``` bash
source .venv/bin/activate
```

Run the bot:

``` bash
uv run python bot.py
```

You should see:

    ⚡️ Bolt app is running!

------------------------------------------------------------------------

## 🛠 Slack Setup

### 1. Enable Socket Mode

Slack → App Settings → **Socket Mode → Enable**

### 2. Enable Event Subscriptions

Slack → App Settings → **Event Subscriptions → Enable**

Subscribe to bot events:

-   `message.channels`
-   `message.groups`
-   `app_mention` (optional)

### 3. Add the bot to a Slack channel

In Slack, type:

    @MobbinGPT

→ click **Invite to channel**

------------------------------------------------------------------------

## 🔮 How It Works

1.  Bot receives every message event.
2.  Tracks timestamps per channel (in-memory).
3.  If enough messages appear within a given time window:
    -   Fetches recent Slack conversation history.
    -   Builds a context prompt.
4.  Sends prompt to **Gemini**.
5.  Replies with a roast based on the context.

------------------------------------------------------------------------

## ⚠️ Limitations

-   Bot is designed for humor, not abuse.
-   Gemini output may vary.
-   In-memory tracking resets when the bot is restarted.

------------------------------------------------------------------------

## 💡 Future Improvements

-   Add mute commands (`!mute 10`)
-   Add custom roast modes
-   Add slash commands
-   Add a persistent database

------------------------------------------------------------------------

## 🧑‍💻 Author

Created by **Robin Sundman Nilsson**

------------------------------------------------------------------------

## 🔥 License

No restrictions. Have fun.
