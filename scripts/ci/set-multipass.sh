#!/bin/sh

vm_start() {
    multipass launch
}

vm_exec() {
    multipass exec "$1" -c "$2"
}

