from typing import Self
import pydantic
import ipaddress


class Base(pydantic.BaseModel):
    pass


class Interface(Base):
    network: str
    address: list[ipaddress.IPv4Address] | None = None

    @pydantic.field_validator("address", mode="before")
    @classmethod
    def ensure_list(cls, v: str | list[str]) -> list[str]:
        if not isinstance(v, list):
            v = [v]

        return v


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
    gateway: ipaddress.IPv4Address | None = None
    offset: int = 1
    autogateway: bool = True

    _addrcount: int = 0
    _allocated: set[ipaddress.IPv4Address] = set()

    @pydantic.model_validator(mode="after")
    def validate_gateway(self) -> Self:
        if self.gateway is None and self.autogateway:
            self.gateway = self._allocate_one(self.cidr[1])
        elif self.gateway is not None:
            if self.gateway not in self.cidr:
                raise ValueError(f"{self.gateway} is not contained by {self.cidr}")

            self.allocate(self.gateway)

        return self

    def __next__(self) -> ipaddress.IPv4Address:
        while True:
            addr = self.cidr[self.offset + self._addrcount]
            self._addrcount += 1
            if addr in self._allocated:
                continue
            self._allocated.add(addr)
            break

        return addr

    def _allocate_one(self, addr: ipaddress.IPv4Address) -> ipaddress.IPv4Address:
        addr = ipaddress.IPv4Address(addr)

        if addr not in self.cidr:
            raise ValueError(f"{addr} is not contained by {self.cidr}")

        self._allocated.add(addr)
        return addr

    def allocate(
        self, *addrs: list[ipaddress.IPv4Address]
    ) -> list[ipaddress.IPv4Address]:
        """Mark one or more addresses as in use. Once an address has been
        allocated, a subsequent attempt to allocate it will result in a
        ValueError."""

        return [self._allocate_one(addr) for addr in addrs]

    def seen(addr: ipaddress.IPv4Address) -> bool:
        return addr in self._allocated


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
    networks: dict[str, Network]
    common: Common | None = None
    hosts: dict[str, Host]

    @pydantic.model_validator(mode="after")
    def validate_interfaces(self) -> Self:
        for host, conf in self.hosts.items():
            for iface in conf.interfaces:
                if iface.network not in self.networks:
                    raise ValueError(f"{iface.network}: unknown network")

                network = self.networks[iface.network]

                if iface.address is None:
                    iface.address = [next(network)]
                else:
                    for address in iface.address:
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
