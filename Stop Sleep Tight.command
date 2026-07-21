#!/bin/zsh
set -u

LABEL="com.sleeptight.receiver"
DOMAIN="gui/$(id -u)"

if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "$DOMAIN/$LABEL"
  print "Sleep Tight receiver stopped. Phone and watch uploads are paused."
else
  print "Sleep Tight receiver is already stopped."
fi

print "Double-click “Start Sleep Tight.command” whenever you want to resume."
