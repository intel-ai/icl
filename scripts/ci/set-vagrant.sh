#!/bin/sh

vm_start() {
    echo "Starting up Vagrant VMs ..."

    cd "$WORKFLOW_DIR"
    vagrant up        
}

vm_exec() {
    vagrant ssh "$1" -c "$2"
}

ensure_vagrant_plugins() {
    if ! vagrant plugin list | grep -q vagrant-proxyconf; then
        vagrant plugin install vagrant-proxyconf
    fi
    if ! vagrant plugin list | grep -q vagrant-reload; then
        vagrant plugin install vagrant-reload
    fi
    if ! vagrant plugin list | grep -q vagrant-scp; then
        vagrant plugin install vagrant-scp
    fi
}

ensure_vagrant_plugins

