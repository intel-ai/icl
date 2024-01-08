#!/bin/sh

set -e
set -vx

. scripts/ci/common.sh

set_env() {
    export AGENT_ID
    export WORKSPACE_DIR

    export X1_PREFIX="$WORKFLOW_PREFIX"

    export X1_LIBVIRT_DEFAULT_PREFIX="$WORKFLOW_PREFIX_ID"
    export VAGRANT_DEFAULT_PROVIDER=libvirt
    export no_proxy=localtest.me,.localtest.me,$no_proxy

    echo "X1_LIBVIRT_DEFAULT_PREFIX: $X1_LIBVIRT_DEFAULT_PREFIX"
    echo "X1_K8S_EXTRA_SETTINGS_FILE: $X1_K8S_EXTRA_SETTINGS_FILE"
}

function vm_cleanup {
    cd "$WORKFLOW_DIR"
    echo "Copying logs ..."
    vagrant scp jumphost:x1/logs "$WORKSPACE_DIR" || true
    echo "Cleaning up Vagrant VMs ..."
    vagrant destroy -f || true
}

vm_clean_before() {
    cd "$WORKFLOW_DIR"

    ps -ef
    echo "Cleaning vagrant"
    vagrant destroy -f || true

    echo "Cleaning domains"
    virsh list --all
    virsh list --all --name | grep -E "^${X1_LIBVIRT_DEFAULT_PREFIX}-" | xargs --no-run-if-empty -n 1 virsh destroy || true
    virsh list --all --name | grep -E "^${X1_LIBVIRT_DEFAULT_PREFIX}-" | xargs --no-run-if-empty -n 1 virsh undefine || true

    echo "Cleaning nets"
    virsh net-list --all
    virsh net-destroy "${X1_LIBVIRT_DEFAULT_PREFIX}-CLUSTER_1" || true
    virsh net-undefine "${X1_LIBVIRT_DEFAULT_PREFIX}-CLUSTER_1" || true

    echo "Cleanup finished"
}

generate_key() {
    test -f ~/.ssh/id_rsa || ssh-keygen -q -b 2048 -t rsa -N '' -C 'cluster key' -f ~/.ssh/id_rsa
    mkdir -p generated
    ln -snf ~/.ssh/id_rsa generated/
    ln -snf ~/.ssh/id_rsa.pub generated/
}

. "$WORKFLOW_DIR"/init.sh

set_env
vm_clean_before
generate_key

