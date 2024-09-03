import argparse
import ipaddress
import jinja2
import networkx as nx
import pathlib
import yaml

from makelab import models


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--output-directory", "-o", default=".", type=pathlib.Path)
    p.add_argument("topology", default="topology.yaml", nargs="?")
    return p.parse_args()


def generate_host_configs(topology: models.Topology) -> dict[str, models.RealizedHost]:
    allconf = {}
    for network, conf in topology.networks.items():
        if conf.gateway is None:
            conf.gateway = conf.cidr[1]

    for name, conf in topology.hosts.items():
        interfaces = []
        routes = []
        for n, iface in enumerate(conf.interfaces):
            network = topology.networks[iface.network]
            dev = f"eth{n}"

            if iface.address is None:
                addrs = [next(network)]
            else:
                addrs = network.allocate(*iface.address)

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

    return allconf


def generate_diagram(topology, path):
    G = nx.Graph()

    for name in topology.networks:
        G.add_node(name)

    for name, conf in topology.hosts.items():
        G.add_node(name, shape="box")
        for iface in conf.interfaces:
            G.add_edge(name, iface.network)

    nx.drawing.nx_pydot.write_dot(G, path)


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

    allconf = generate_host_configs(topology)

    for name, hostconf in allconf.items():
        with (args.output_directory / f"{name}.startup").open("w") as fd:
            fd.write(startup.render(host=hostconf, topology=topology))

    shared_dir = args.output_directory / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)
    with (shared_dir / "hosts").open("w") as fd:
        fd.write(hosts.render(hosts=allconf))

    generate_diagram(topology, args.output_directory / "topology.dot")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
