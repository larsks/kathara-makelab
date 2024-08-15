import ipaddress
import pytest

from makelab import models


@pytest.fixture
def network():
    return models.Network(cidr="192.168.1.0/28")


def test_network_allocate_simple(network):
    addr = next(network)
    assert addr == ipaddress.IPv4Address("192.168.1.1")


def test_network_allocate_explicit(network):
    network.allocate("192.168.1.1")
    network.allocate("192.168.1.2")
    addr = next(network)
    assert addr == ipaddress.IPv4Address("192.168.1.3")


def test_network_allocate_all(network):
    addrs = network.allocate_all(["192.168.1.1", "192.168.1.2", "192.168.1.3"])
    assert all(isinstance(addr, ipaddress.IPv4Address) for addr in addrs)
    addr = next(network)
    assert addr == ipaddress.IPv4Address("192.168.1.4")


def test_network_allocate_conflict_explicit(network):
    network.allocate("192.168.1.1")

    with pytest.raises(ValueError):
        network.allocate("192.168.1.1")


def test_network_allocate_conflict_implicit(network):
    next(network)

    with pytest.raises(ValueError):
        network.allocate("192.168.1.1")


def test_network_allocate_failure(network):
    with pytest.raises(IndexError):
        while True:
            next(network)
