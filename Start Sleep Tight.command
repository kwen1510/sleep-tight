#!/bin/zsh
set -u

LABEL="com.sleeptight.receiver"
DOMAIN="gui/$(id -u)"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DASHBOARD="http://127.0.0.1:8766/dashboard.html"

if ! launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
  if [[ ! -f "$PLIST" ]]; then
    print "Sleep Tight is not installed yet."
    print "Run: python3 tools/setup_sleep_tight.py --no-build"
    exit 1
  fi
  launchctl bootstrap "$DOMAIN" "$PLIST"
fi

if ! curl --silent --fail --max-time 2 "http://127.0.0.1:8766/api/v1/health" >/dev/null; then
  launchctl kickstart -k "$DOMAIN/$LABEL"
fi

for attempt in {1..10}; do
  if curl --silent --fail --max-time 1 "http://127.0.0.1:8766/api/v1/health" >/dev/null; then
    open "$DASHBOARD"
    print "Sleep Tight is ready and accepting phone/watch uploads."
    print "It will remain active in the background."
    exit 0
  fi
  sleep 1
done

print "The receiver did not become ready. Check computer/receiver-error.log."
exit 1
