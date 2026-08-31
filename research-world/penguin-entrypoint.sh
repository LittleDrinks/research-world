#!/bin/sh
set -eu

seed_file=/penguin-data/.seed-admin-password
if [ ! -s "$seed_file" ]; then
  umask 077
  python -c 'import secrets; print(secrets.token_urlsafe(32))' >"$seed_file"
fi
chmod 600 "$seed_file"
export PENGUIN_SEED_ADMIN_PASSWORD="$(cat "$seed_file")"
exec "$@"
