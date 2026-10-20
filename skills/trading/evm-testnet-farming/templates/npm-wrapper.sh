#!/bin/bash
# Template: Shell wrapper for npm scripts that need .env variables
# Usage: Copy this, rename to your-command.sh, update the npm run target

# Load .env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check required env vars (customize this list)
if [ -z "$RPC_URL" ]; then
    echo "❌ RPC_URL not set!"
    echo "   Add to .env or: export RPC_URL=\"your-rpc-url\""
    exit 1
fi

# Optional: Display config
echo "🌐 RPC: $RPC_URL"
echo ""

# Run the npm script (change 'farm' to your target)
npm run farm
