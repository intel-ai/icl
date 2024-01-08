#!/bin/sh

set_env() {
    AGENT_ID=$(hostname | sed -e 's/.*[^0-9]//')
    AGENT_ID=${AGENT_ID:-100}

    WORKSPACE_DIR=$(dirname "$0")/../..
    WORKSPACE_DIR=$(cd "$WORKSPACE_DIR" && pwd -P)

    WORKFLOW_PREFIX=$(basename "$0" .sh)
    WORKFLOW_DIR="$WORKSPACE_DIR/$WORKFLOW_PREFIX"

    WORKFLOW_PREFIX_ID="$WORKFLOW_PREFIX-$AGENT_ID"

    X1_K8S_EXTRA_SETTINGS_FILE="$WORKSPACE_DIR/x1-cluster-profiles/profiles/ci.yaml"
    no_proxy=localtest.me,.localtest.me,$no_proxy

    export X1_K8S_EXTRA_SETTINGS_FILE
    export no_proxy
 
    echo "WORKSPACE_DIR: $WORKSPACE_DIR"
    echo "X1_K8S_EXTRA_SETTINGS_FILE: $X1_K8S_EXTRA_SETTINGS_FILE"
}

run_kind() {
    vm_start
    vm_exec jumphost "./x1/scripts/deploy/kind.sh"
    vm_exec jumphost "./x1/scripts/deploy/kind.sh --console ./scripts/ccn/test.sh"
    vm_cleanup
}


