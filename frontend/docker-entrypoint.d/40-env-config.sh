#!/bin/sh
set -eu

: "${API_URL:=/benchmark}"

cat > /usr/share/nginx/html/js/env.js <<EOF
window.APP_CONFIG = {
  API_URL: "${API_URL}"
};
EOF
