import ipaddress
import pytest

from makelab import models


@pytest.fixture
def network_no_gateway():
    return models.Network(cidr="192.168.1.0/28", autogateway=False)


@pytest.fixture
def network():
    return models.Network(cidr="192.168.1.0/28")


def test_network_allocate_simple(network_no_gateway):
    addr = next(network_no_gateway)
    assert addr == ipaddress.IPv4Address("192.168.1.1")


def test_network_allocate_with_gateway(network):
    addr = next(network)
    assert addr == ipaddress.IPv4Address("192.168.1.2")


def test_network_allocate_explicit(network):
    network.allocate("192.168.1.2", "192.168.1.3")
    addr = next(network)
    assert addr == ipaddress.IPv4Address("192.168.1.4")


def test_network_allocate_no_addresses_left(network):
    with pytest.raises(IndexError):
        while True:
            next(network)


def test_network_allocate_bad_address(network):
    with pytest.raises(ValueError):
        network.allocate("192.168.2.1")


def test_network_bad_gateway():
    with pytest.raises(ValueError):
        models.Network(cidr="192.168.1.1/24", gateway="192.168.2.1")


def test_interface():
    with pytest.raises(ValueError):
        models.Interface()

    with pytest.raises(ValueError):
        models.Interface(network="test", address="badvalue")

    models.Interface(network="test")
    iface = models.Interface(network="test", address="192.168.1.1")
    assert iface.address == [ipaddress.IPv4Address("192.168.1.1")]


def test_topology_interfaces():
    topology = models.Topology(
        networks={
            "net0": models.Network(cidr="192.168.1.0/28"),
        },
        hosts={
            "host0": models.Host(
                interfaces=[
                    models.Interface(network="net0"),
                ]
            ),
            "host1": models.Host(
                interfaces=[
                    models.Interface(network="net0", address="192.168.1.10"),
                ]
            ),
        },
    )
    assert topology.hosts["host0"].interfaces[0].address[0] == ipaddress.IPv4Address(
        "192.168.1.2"
    )
    assert topology.hosts["host1"].interfaces[0].address[0] == ipaddress.IPv4Address(
        "192.168.1.10"
    )
