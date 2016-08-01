#! /bin/bash


# Set up the required environment for Stolos scripts to run

if [ $DOCKER_HOST == ""]; then
    echo 'DOCKER_HOST is not defined';
    exit 1;
fi

if [ $STOLOS_PROJECT_ID == ""]; then
    echo 'STOLOS_PROJECT_ID is not defined';
    exit 1;
fi

export DOCKER_TLS_VERIFY="1"
export DOCKER_CERT_PATH="$(pwd)/.stolos"
