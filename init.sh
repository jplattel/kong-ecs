#!/bin/bash

set -eu
docker
[ -e /var/run/docker.sock ]

HOST_IP=$(curl -s 169.254.169.254/1.0/meta-data/local-ipv4)
OUTER_PORT=$(docker inspect -f '{{index .NetworkSettings.Ports "7946/tcp" 0 "HostPort"}}' $(hostname))

KONG_CLUSTER_ADVERTISE="$HOST_IP:$OUTER_PORT" kong start
