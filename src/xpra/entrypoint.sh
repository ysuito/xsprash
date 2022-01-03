#!/bin/sh

if [ $1 = "client" ]; then
  exec bash -c "xpra attach tcp://host.containers.internal:${XPRA_PORT}/${XPRA_DISPLAY}"
elif [ $1 = "server" ]; then
  chmod 1777 /tmp/.X11-unix/
  exec bash -c "xpra start :$XPRA_DISPLAY --bind-tcp=0.0.0.0:$XPRA_PORT --start=\"xhost +SI:localuser:root\" --no-daemon"
else
  exec bash -c "$@"
fi
