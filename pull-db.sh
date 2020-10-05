#!/bin/bash

MONGO_HOST=<MONGO_HOST>
MONGO_USER=<MONGO_USER>
MONGO_PASSWORD=<MONGO_PASSWORD>
MONGO_PRODUCTION_DB=<MONGO_PRODUCTION_DB>
MONGO_DEVELOPEMENT_DB=<MONGO_DEVELOPEMENT_DB>
DUMP_FOLDER=/tmp/pull-db/
RESTORE_FOLDER=/tmp/pull-db/ebl

mongodump -h $MONGO_HOST \
    -d $MONGO_PRODUCTION_DB \
    --forceTableScan \
    --excludeCollectionsWithPrefix=fragments_backup \
    --excludeCollectionsWithPrefix=fragments_bakcup \
    --excludeCollectionsWithPrefix=bibliography_backup \
    --excludeCollectionsWithPrefix=bibliography_backup \
    --excludeCollectionsWithPrefix=orphan \
    --excludeCollectionsWithPrefix=signs_backup \
    --excludeCollectionsWithPrefix=signs_with_invalid \
    --excludeCollectionsWithPrefix=texts_backup \
    --excludeCollectionsWithPrefix=words_backup \
    --excludeCollection=changelog \
    --excludeCollection=folios.files \
    --excludeCollection=folios.chunks \
    --excludeCollection=photos.files \
    --excludeCollection=photos.chunks \
    -u $MONGO_USER -p $MONGO_PASSWORD \
    --ssl --sslAllowInvalidCertificates \
    -o $DUMP_FOLDER


mongorestore -h rs-ebl1/lmkwitg-ebl01.srv.mwn.de:27017,lmkwitg-ebl02.srv.mwn.de:27018  \
    -d $MONGO_DEVELOPEMENT_DB \
     -u $MONGO_USER -p $MONGO_PASSWORD \
    --ssl --sslAllowInvalidCertificates \
    --authenticationDatabase ebl \
    --drop \
    $RESTORE_FOLDER


rm -rf $RESTORE_FOLDER
