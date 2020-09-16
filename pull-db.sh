#!/bin/bash

defaultTempFolder="/tmp/pull-db"
read -p "Download folder [$defaultTempFolder]: " tempFolder
tempFolder=${tempFolder:-$defaultTempFolder}

read -p "Source host: " sourceHost

defaultSourceDb="ebl"
read -p "Database [$defaultSourceDb]: " sourceDb
sourceDb=${sourceDb:-$defaultSourceDb}

read -p "Source user name: " sourceUser
read -sp "Source password: " sourcePassword
echo


defaultTargetHost="localhost:27017"
read -p "Target host [$defaultTargetHost]: " targetHost
targetHost=${targetHost:-$defaultTargetHost}

read -p "Target user name (Leave blank if target has no authentication.): " targetUser
if [ $targetUser ]
then
    read -sp "Target password:" targetPassword
    echo
fi


mongodump -h $sourceHost \
    -d $sourceDb \
    --excludeCollection=changelog \
    --excludeCollection=folios.files \
    --excludeCollection=folios.chunks \
    --excludeCollection=photos.files \
    --excludeCollection=photos.chunks \
    -u $sourceUser -p $sourcePassword \
    --ssl --sslAllowInvalidCertificates \
    -o $tempFolder


if [ $targetUser ]
then
    mongorestore -h $targetHost -u $targetUser -p $targetPassword $tempFolder
else
    mongorestore -h $targetHost --drop $tempFolder
fi
