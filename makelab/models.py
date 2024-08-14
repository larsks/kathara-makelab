from typing import Self
import pydantic
import ipaddress


class Base(pydantic.BaseModel):
    pass


class Connection(Base):
    network: str
    address: str | list[str] | None = None


class Host(Base):
    autogateway: bool = True
    connections: list[Connection]
    routes: list[str] = pydantic.Field(default_factory=list)
    startup: str | None = None


class Network(Base):
    cidr: ipaddress.IPv4Network
    gateway: str | None = None
    offset: int = 2


class Metadata(Base):
    description: str | None = None
    version: str | None = None
    author: str | None = None
    email: str | None = None
    url: str | None = None


class Topology(Base):
    metadata: Metadata | None = None
    networks: dict[str, Network | None]
    hosts: dict[str, Host]

    @pydantic.model_validator(mode="after")
    def check_networks(self) -> Self:
        for host, conf in self.hosts.items():
            for connection in conf.connections:
                if connection.network not in self.networks:
                    raise ValueError(f"{connection.network}: unknown network")
        return self


class Interface(Base):
    device: str
    network: str
    prefixlen: int
    addresses: list[ipaddress.IPv4Address]


class NetworkConfiguration(Base):
    routes: list[str]
    interfaces: list[Interface]
