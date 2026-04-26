#!/usr/bin/env bash
# Daily PostgreSQL backup, uploads to S3 with retention.
# Run via cron host or as a CronJob in K8s.
set -euo pipefail

: "${POSTGRES_HOST:=postgres}"
: "${POSTGRES_USER:=smartbarrel}"
: "${POSTGRES_DB:=smartbarrel_db}"
: "${BACKUP_BUCKET:=smartbarrel-backups}"
: "${RETENTION_DAYS:=30}"

ts=$(date -u +%F_%H-%M)
out="/tmp/${POSTGRES_DB}_${ts}.dump"

echo "Dumping ${POSTGRES_DB} → ${out}"
pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --format=custom --file="$out"

echo "Uploading to s3://${BACKUP_BUCKET}/postgres/daily/${ts}.dump"
aws s3 cp "$out" "s3://${BACKUP_BUCKET}/postgres/daily/${ts}.dump"

echo "Cleaning local dump"
rm -f "$out"

echo "Trimming objects older than ${RETENTION_DAYS}d"
cutoff=$(date -u -v-${RETENTION_DAYS}d +%F 2>/dev/null \
        || date -u -d "${RETENTION_DAYS} days ago" +%F)
aws s3 ls "s3://${BACKUP_BUCKET}/postgres/daily/" |
  awk -v c="$cutoff" '$1 < c {print $4}' |
  while read -r key; do
    aws s3 rm "s3://${BACKUP_BUCKET}/postgres/daily/${key}"
  done

echo "Done."
