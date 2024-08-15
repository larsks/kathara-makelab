# kathara-makelab

Generate [Kathara] labs from YAML manifests.


[kathara]: https://github.com/KatharaFramework/Kathara

## Usage

```
usage: makelab [-h] [--output-directory OUTPUT_DIRECTORY] [topology]

positional arguments:
  topology

options:
  -h, --help            show this help message and exit
  --output-directory OUTPUT_DIRECTORY, -o OUTPUT_DIRECTORY
```

## Installation

```
pip install git+https://github.com/larsks/kathara-makelab
```

## Description

The `makelab` command reads a YAML manifest and generates a `lab.conf` and associated `*.startup` files. This allows you to encapsulate a complete lab in a single file, making it easier to share with others.

## Examples

## Simple

The [`simple.yaml`](examples/simple.yaml) shows how to create a simple topology consisting of two hosts and a router.

```yaml
metadata:
  description: This demonstrates a simple topology with one router, two networks, and three nodes.
  author: Lars Kellogg-Stedman
  url: https://github.com/larsks/kathara-makelab

networks:
  net0:
    cidr: 192.168.100.0/24
  net1:
    cidr: 192.168.101.0/24

common:
  startup: |
    cat /shared/hosts >> /etc/hosts

hosts:
  router0:
    autogateway: false
    interfaces:
      - network: net0
      - network: net1
  node0:
    interfaces:
    - network: net0
  node1:
    interfaces:
    - network: net0
  node2:
    interfaces:
    - network: net1
```

## Featureful

The [`featureful.yaml`](examples/featureful.yaml) demonstrates most of the options available in a makelab manifest.

```yaml
metadata:
  description: This demonstrates several features of makelab.
  author: Lars Kellogg-Stedman
  url: https://github.com/larsks/kathara-makelab

networks:
  net0:
    cidr: 192.168.100.0/24
    gateway: 192.168.100.254
    offset: 10
  net1:
    cidr: 192.168.101.0/24
    gateway: 192.168.101.254
    offset: 10

common:
  # makelab generates a hosts file in shared/hosts. This startup script appends
  # that to /etc/hosts in the container so that we can refer to hosts in the
  # lab by name. Note that hostnames are created from the host name and the
  # interface name associated with the address, so we get names like `node0-eth0`.
  startup: |-
    cat /shared/hosts >> /etc/hosts

hosts:
  router0:
    autogateway: false
    interfaces:
      - network: net0
        address: 192.168.100.254
      - network: net1
        address: 192.168.101.254
  node0:
    interfaces:
    - network: net0
    startup: |-
      echo nameserver 8.8.8.8 > /etc/resolv.conf

    # With `bridged: true`, the container will already have a configured
    # default route (using the docker bridged network) before the startup
    # script runs. We need to delete that before we can set our own.
    startup_early: |-
      ip route delete default
    options:
      # See https://github.com/KatharaFramework/Kathara/blob/main/docs/kathara-lab.conf.5.ronn
      # for documentation on the available options.
      shell: /bin/sh
      image: docker.io/alpine:latest
      bridged: true
      # List options will be repeated multiple times, once for each value.
      # E.g., this will result in:
      #
      # node0[port]="8080:8080"
      # node0[port]="2222:22"
      port:
        - "8080:8080"
        - "2222:22"
  node1:
    interfaces:
    - network: net0
    options:
      env:
      - SOMEVAR=foo
      - ANOTHERVAR=bar
  node2:
    interfaces:
    - network: net1
      address: 192.168.101.37
    options:
      env: SOMEVAR=foo
```
