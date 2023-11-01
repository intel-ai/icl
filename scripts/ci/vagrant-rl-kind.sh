#!/usr/bin/env bash

# This script is called from GitHub workflow.
# Single node X1 with Kind on Vagrant VM with Rocky Linux.

. scripts/ci/init.sh

start_vagrant
vagrant ssh jumphost -c "./x1/scripts/deploy/kind.sh"
vagrant ssh jumphost -c "./x1/scripts/deploy/kind.sh --console ./scripts/ccn/test.sh"

