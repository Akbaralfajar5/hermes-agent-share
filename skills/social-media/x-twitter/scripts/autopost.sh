#!/usr/bin/env bash
# X/Twitter Auto-Post Cron Script
# Schedule: crontab -e → add lines like:
#   0 7 * * * /path/to/autopost.sh morning
#   0 12 * * * /path/to/autopost.sh midday  
#   0 19 * * * /path/to/autopost.sh evening
#
# Requires: .env.local with X API credentials in SKILL_DIR

SKILL_DIR="$HOME/.hermes/skills/social-media/x-twitter"
XJS="node $SKILL_DIR/x.js"
SLOT="${1:-morning}"
LOG="$HOME/x-autopost.log"

# Source credentials
if [ -f "$SKILL_DIR/.env.local" ]; then
  export $(grep -v '^#' "$SKILL_DIR/.env.local" | xargs)
fi

post_tweet() {
  local text="$1"
  echo "[$(date)] Posting ($SLOT): ${text:0:50}..." >> "$LOG"
  $XJS post "$text" >> "$LOG" 2>&1
  echo "[$(date)] Exit code: $?" >> "$LOG"
}

# --- CONTENT GOES HERE ---
# Replace with actual content generation logic.
# For AI-generated content, call hermes or a local script.
# Example static post:

case "$SLOT" in
  morning)
    post_tweet "🌅 Good morning! Crypto market update coming soon... #crypto #BTC"
    ;;
  midday)
    post_tweet "💡 Tip of the day: Always DYOR before investing. #crypto #trading"
    ;;
  evening)
    post_tweet "📊 Market recap: How did your portfolio do today? #crypto"
    ;;
esac
