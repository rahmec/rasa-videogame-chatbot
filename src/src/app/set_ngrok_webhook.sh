#!/bin/bash

# Wait for Ngrok to start and fetch its public URL
NGROK_URL=""
while [ -z "$NGROK_URL" ]; do
  echo "Waiting for ngrok to initialize..."
  sleep 3
  NGROK_URL=$(curl --silent http://ngrok:4040/api/tunnels | jq -r '.tunnels[0].public_url')
done

echo "Ngrok URL: $NGROK_URL"

export WEBHOOK_URL="$NGROK_URL/webhooks/telegram/webhook"

echo "Setting Telegram webhook to $WEBHOOK_URL..."
curl -X POST "https://api.telegram.org/bot$TELEGRAM_API_TOKEN/setWebhook?url=$WEBHOOK_URL"

echo "Webhook set successfully!"
