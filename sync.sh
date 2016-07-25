#! /bin/bash

if [ -z $STOLOS_PROJECT_ID ]; then
    echo 'Please define STOLOS_PROJECT_ID env variable';
    exit 1;
fi

unison -repeat 2 $(pwd) "ssh://stolos-unison//mnt/stolos/${STOLOS_PROJECT_ID}"
