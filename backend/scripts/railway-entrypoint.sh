#!/bin/sh
set -e

if [ "${SERVICE_ROLE:-api}" = "worker" ]; then
  exec celery -A config worker -l info --concurrency "${CELERY_CONCURRENCY:-1}"
fi

exec sh scripts/railway-start.sh
