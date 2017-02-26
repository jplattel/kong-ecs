#!/bin/bash

set -eu

host_ip=$(curl -s 169.254.169.254/1.0/meta-data/local-ipv4)

KONG_CLUSTER_ADVERTISE="$host_ip" kong start
