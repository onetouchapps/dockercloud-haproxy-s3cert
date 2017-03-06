FROM dockercloud/haproxy:1.6.3
RUN pip install --upgrade pip && \
    pip install boto3==1.4.4
COPY haproxy-s3cert /haproxy-s3cert
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/haproxy-s3cert/entrypoint.sh"]
