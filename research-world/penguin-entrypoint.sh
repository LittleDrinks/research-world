#!/bin/sh
set -eu

export PENGUIN_SEED_ADMIN_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
exec "$@"
