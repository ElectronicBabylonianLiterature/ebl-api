FROM ubuntu:latest
#Install Cron
RUN apt-get update
RUN apt-get -y install cron
RUN apt-get -y install mongo-tools
# Add crontab file in the cron directory
ADD crontab /etc/cron.d/hello-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/hello-cron

COPY mongosync.sh /mongosync.sh
RUN chmod 0744 /mongosync.sh
# Create the log file to be able to run tail
RUN touch /var/log/cron.log




# Run the command on container startup
CMD cron && tail -f /var/log/cron.log