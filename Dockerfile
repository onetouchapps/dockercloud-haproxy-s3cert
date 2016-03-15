FROM tutum/haproxy
RUN pip install --upgrade pip && \
    pip install boto3==1.2.1
COPY haproxy-s3cert /haproxy-s3cert
CMD ["/haproxy-s3cert/entrypoint.sh"]
