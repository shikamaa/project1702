FROM gcc:latest

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /uploads
ENTRYPOINT ["/entrypoint.sh"]