FROM alpine:latest

RUN apk add mongodb-tools
ADD mongosync.sh /etc/periodic/daily/mongosync
RUN chmod 0744 /etc/periodic/daily/mongosync 

CMD crond -f -l 8