#!/bin/bash
source ./venv/bin/activate
source ./.env
#celery longterm_scheduler

if [ -z "$DISCORD_BOT_TOKEN" ]; then
  printf 'Enter Discord Bot Token\n'
  read DISCORD_BOT_TOKEN
fi

export DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN
celery -A timestamper.ts_discord worker -P threads

