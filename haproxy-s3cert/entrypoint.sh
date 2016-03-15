#!/bin/bash
set -e
echo "Collecting cert pem from S3"
export DEFAULT_SSL_CERT=`/usr/bin/python /haproxy-s3cert/collect_s3_cert.py`
python /haproxy/main.py
