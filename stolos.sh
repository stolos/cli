#! /bin/bash

if [ -z $STOLOS_PROJECT_ID ]; then
    echo 'Please define STOLOS_PROJECT_ID env variable';
    exit 1;
fi

exec docker-compose -p ${STOLOS_PROJECT_ID} "$@"
