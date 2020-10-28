#!/bin/bash

defaultTempFolder="/tmp/pull-db"
read -p "Download folder [$defaultTempFolder]: " tempFolder
tempFolder=${tempFolder:-$defaultTempFolder}

defaultSourceHost=$PULL_DB_DEFAULT_SOURCE_HOST
read -p "Source host [$defaultSourceHost]: " sourceHost
sourceHost=${sourceHost:-$defaultSourceHost}

defaultSourceDb="ebl"
read -p "Database [$defaultSourceDb]: " sourceDb
sourceDb=${sourceDb:-$defaultSourceDb}

defaultSourceUser=$PULL_DB_DEFAULT_SOURCE_USER
defaultSourcePassword=$PULL_DB_DEFAULT_SOURCE_PASSWORD
read -p "Source user name [$defaultSourceUser]: " sourceUser
read -sp "Source password [${defaultSourcePassword//?/*}]: " sourcePassword
sourceUser=${sourceUser:-$defaultSourceUser}
sourcePassword=${sourcePassword:-$defaultSourcePassword}
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

mkdir -p $tempFolder

mongodump -h $sourceHost \
    -d $sourceDb \
    --forceTableScan \
    --excludeCollection=changelog \
    --excludeCollection=folios.files \
    --excludeCollection=folios.chunks \
    --excludeCollection=photos.files \
    --excludeCollection=photos.chunks \
    --excludeCollectionsWithPrefix=fragments_backup \
    -u $sourceUser -p $sourcePassword \
    --ssl --sslAllowInvalidCertificates \
    -o $tempFolder


if [ $targetUser ]
then
    mongorestore -h $targetHost \
        -u $targetUser -p $targetPassword \
        --authenticationDatabase $sourceDb \
        --drop \
        $tempFolder
else
    mongorestore -h $targetHost --drop $tempFolder
fi
