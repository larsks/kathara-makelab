import argparse
import ipaddress
import jinja2
import os
import pathlib
import tempfile
import yaml

from makelab import models


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--output-directory", "-o", default=".", type=pathlib.Path)
    p.add_argument("topology", default="topology.yaml", nargs="?")
    return p.parse_args()


def main():
    args = parse_args()

    with open(args.topology) as fd:
        raw = yaml.safe_load(fd)

    topology = models.Topology.model_validate(raw)

    env = jinja2.Environment(loader=jinja2.PackageLoader(__package__))
    lab = env.get_template("lab.conf.j2")
    startup = env.get_template("startup.j2")

    with (args.output_directory / "lab.conf").open("w") as fd:
        fd.write(lab.render(topology=topology))

    nextaddr = {}
    for network, conf in topology.networks.items():
        nextaddr[network] = conf.offset
        if conf.gateway is None:
            conf.gateway = conf.cidr[1]

    for host, conf in topology.hosts.items():
        interfaces = []
        routes = []
        for n, connection in enumerate(conf.connections):
            network = topology.networks[connection.network]
            dev = f"eth{n}"

            if connection.address is None:
                addrs = network.cidr[nextaddr[connection.network]]
                nextaddr[connection.network] += 1
            else:
                addrs = connection.address

            if not isinstance(addrs, list):
                addrs = [addrs]

            addrs = [ipaddress.IPv4Address(addr) for addr in addrs]
            interfaces.append(
                models.Interface(
                    device=dev,
                    network=connection.network,
                    addresses=addrs,
                    prefixlen=network.cidr.prefixlen,
                )
            )

            if conf.autogateway:
                gateway = topology.networks[connection.network].gateway
                routes.append(f"default via {gateway}")

        routes.extend(conf.routes)
        netconf = models.NetworkConfiguration(interfaces=interfaces, routes=routes)

        with (args.output_directory / f"{host}.startup").open("w") as fd:
            fd.write(startup.render(netconf=netconf))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
