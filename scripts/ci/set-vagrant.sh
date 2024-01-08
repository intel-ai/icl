#!/bin/sh

vm_start() {
    echo "Starting up Vagrant VMs ..."

    cd "$WORKFLOW_DIR"
    vagrant up        
}

vm_exec() {
    vagrant ssh "$1" -c "$2"
}

