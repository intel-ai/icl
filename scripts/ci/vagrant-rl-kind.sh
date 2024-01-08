#!/usr/bin/env bash

# This script is called from GitHub workflow.
# Single node ICL cluster with Kind on Vagrant VM with Rocky Linux.

. scripts/ci/init.sh

run_kind

