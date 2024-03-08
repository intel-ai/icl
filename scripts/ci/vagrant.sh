#!/usr/bin/env bash

# This script is called from GitHub workflow.

. scripts/ci/init.sh

export X1_NOMAAS_CLUSTER_SUBNET_PREFIX=172.31.$AGENT_ID
export no_proxy=${X1_NOMAAS_CLUSTER_SUBNET_PREFIX}.0/24,$no_proxy

echo X1_LIBVIRT_DEFAULT_PREFIX: $X1_LIBVIRT_DEFAULT_PREFIX
echo X1_NOMAAS_CLUSTER_SUBNET_PREFIX: $X1_NOMAAS_CLUSTER_SUBNET_PREFIX

vm_start
vm_exec ./everything.sh

RESULT=0
if ! vm_exec ./test.sh; then
  RESULT=1
fi

vm_copy_logs
vm_cleanup

exit $RESULT
