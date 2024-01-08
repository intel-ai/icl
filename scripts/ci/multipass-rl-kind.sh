#!/usr/bin/env bash

# This script is called from GitHub workflow.
# Single node ICL cluster with Kind on Multipass VM with Rocky Linux.

. scripts/ci/init.sh

start_vagrant
multipass exec jumphost -c "./x1/scripts/deploy/kind.sh"
multipass exec jumphost -c "./x1/scripts/deploy/kind.sh --console ./scripts/ccn/test.sh"

