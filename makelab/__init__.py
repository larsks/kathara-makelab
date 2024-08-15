import argparse
import ipaddress
import jinja2
import pathlib
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

    env = jinja2.Environment(loader=jinja2.PackageLoader(__package__), trim_blocks=True)
    lab = env.get_template("lab.conf.j2")
    startup = env.get_template("startup.j2")
    hosts = env.get_template("hosts.j2")

    with (args.output_directory / "lab.conf").open("w") as fd:
        fd.write(lab.render(topology=topology))

    nextaddr = {}
    allconf = {}
    for network, conf in topology.networks.items():
        nextaddr[network] = conf.offset
        if conf.gateway is None:
            conf.gateway = conf.cidr[1]

    for name, conf in topology.hosts.items():
        interfaces = []
        routes = []
        for n, iface in enumerate(conf.interfaces):
            network = topology.networks[iface.network]
            dev = f"eth{n}"

            if iface.address is None:
                addrs = network.cidr[nextaddr[iface.network]]
                nextaddr[iface.network] += 1
            else:
                addrs = iface.address

            if not isinstance(addrs, list):
                addrs = [addrs]

            addrs = [ipaddress.IPv4Address(addr) for addr in addrs]
            interfaces.append(
                models.RealizedInterface(
                    device=dev,
                    network=iface.network,
                    addresses=addrs,
                    prefixlen=network.cidr.prefixlen,
                )
            )

            if conf.autogateway:
                gateway = topology.networks[iface.network].gateway
                routes.append(f"default via {gateway}")

        routes.extend(conf.routes)
        hostconf = models.RealizedHost(
            name=name,
            host=conf,
            interfaces=interfaces,
            routes=routes,
        )
        allconf[name] = hostconf

        with (args.output_directory / f"{name}.startup").open("w") as fd:
            fd.write(startup.render(host=hostconf, topology=topology))

    shared_dir = args.output_directory / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)
    with (shared_dir / "hosts").open("w") as fd:
        fd.write(hosts.render(hosts=allconf))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
