#!/bin/bash

PAYLOAD=$(source ~/fhoopz/venv/bin/activate; python3 ~/fhoopz/fantasy_update.py; deactivate); DATA_START='{"channel":"FAKEID", "text":"'; DATA_END='"}'; curl -X POST -H 'Authorization: Bearer lmaoooooooo' -H 'Content-type: application/json' --data "$DATA_START$PAYLOAD$DATA_END" https://slack.com/api/chat.postMessage;

# hockey-dev channel id: FAKE_ID
# prod channel id: OTHER_FAKE_ID
