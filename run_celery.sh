#!/bin/bash
source ./venv/bin/activate

set -a # automatically export all variables
source ./.env
set +a
#celery longterm_scheduler

if [ -z "$DISCORD_BOT_TOKEN" ]; then
  printf 'Enter Discord Bot Token\n'
  read DISCORD_BOT_TOKEN
fi

celery -A timestamper.ts_discord worker -P threads
