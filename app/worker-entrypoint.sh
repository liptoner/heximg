#!/bin/sh

celery -A heximg worker -l INFO

exec "$@"