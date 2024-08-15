from typing import Self
import pydantic
import ipaddress


class Base(pydantic.BaseModel):
    pass


class Interface(Base):
    network: str
    address: str | list[str] | None = None


class Host(Base):
    autogateway: bool = True
    interfaces: list[Interface]
    routes: list[str] = pydantic.Field(default_factory=list)
    startup: str | None = None
    image: str | None = None


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
        return self


class RealizedInterface(Base):
    device: str
    network: str
    prefixlen: int
    addresses: list[ipaddress.IPv4Address]


class HostConfiguration(Base):
    name: str
    routes: list[str]
    interfaces: list[RealizedInterface]
    startup: str | None
