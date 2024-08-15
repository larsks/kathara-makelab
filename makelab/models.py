from typing import Self
import pydantic
import ipaddress


class Base(pydantic.BaseModel):
    pass


class Interface(Base):
    network: str
    address: ipaddress.IPv4Address | list[ipaddress.IPv4Address] | None = None


class Options(Base):
    image: str | None = None
    mem: str | None = None
    bridged: bool | None = None
    cpus: float | None = None
    ipv6: bool | None = None
    exec: str | None = None
    shell: str | None = None
    num_terms: int | None = None

    sysctl: str | list[str] | None = None
    env: str | list[str] | None = None
    port: str | list[str] | None = None


class Host(Base):
    autogateway: bool = True
    interfaces: list[Interface]
    routes: list[str] = pydantic.Field(default_factory=list)
    startup: str | None = None
    startup_early: str | None = None
    options: Options | None = None


class Network(Base):
    cidr: ipaddress.IPv4Network
    gateway: str | None = None
    offset: int = 1


class Metadata(Base):
    description: str | None = None
    version: str | None = None
    author: str | None = None
    email: str | None = None
    url: str | None = None
    version: str | None = None


class Common(Base):
    startup: str | None = None
    startup_early: str | None = None


class Topology(Base):
    metadata: Metadata | None = None
    networks: dict[str, Network | None]
    common: Common | None = None
    hosts: dict[str, Host]

    @pydantic.model_validator(mode="after")
    def check_networks(self) -> Self:
        for host, conf in self.hosts.items():
            for iface in conf.interfaces:
                if iface.network not in self.networks:
                    raise ValueError(f"{iface.network}: unknown network")

                if iface.address:
                    network = self.networks[iface.network]
                    addrs = iface.address
                    if not isinstance(addrs, list):
                        addrs = [addrs]

                    for address in addrs:
                        if address not in network.cidr:
                            raise ValueError(
                                f"{address} is not contained by {network.cidr}"
                            )
        return self


class RealizedInterface(Base):
    device: str
    network: str
    prefixlen: int
    addresses: list[ipaddress.IPv4Address]


class RealizedHost(Base):
    name: str
    routes: list[str]
    interfaces: list[RealizedInterface]
    host: Host
