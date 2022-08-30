"""
Tests for MEV Boost Relays Whitelist
"""

from ape import reverts, project
from ape.managers.converters import HexConverter
from conftest import (
    assert_single_event,
    suppress_3rd_party_deprecation_warnings,
    Relay,
    ZERO_ADDRESS,
)
from config import lido_dao_agent_address


MAX_RELAYS_NUM = 40  # supposed to correspond to the limit in the contract


TEST_RELAY0 = Relay(
    uri="https://0xb124d80a00b80815397b4e7f1f05377ccc83aeeceb6be87963ba3649f1e6efa32ca870a88845917ec3f26a8e2aa25c77@one.mev-boost-relays.test",
    operator="Relay Operator #1",
    is_mandatory=False,
    description="",
)
TEST_RELAY0_URI_HASH = HexConverter().convert(
    "1e269efbae2680fe1299c248b3dd211bc8a56ced30cd68d88812772c346e463b"  # keccak256
)

TEST_RELAY1 = Relay(
    uri="https://0xafa4c6985aa049fb79dd37010438cfebeb0f2bd42b115b89dd678dab0670c1de38da0c4e9138c9290a398ecd9a0b3110@two.mev-boost-relays.test",
    operator="Relay Operator #2",
    is_mandatory=True,
    description="The relay which is optional",
)
TEST_RELAY1_URI_HASH = HexConverter().convert(
    "133b5f68e62a8abe60fb79a49a87e726af05aacf61b295f04ed20851e8975790"  # keccak256
)


def test_zero_lido_agent(deployer, lido_agent):
    with reverts("zero lido agent address"):
        project.MEVBoostRelayWhitelist.deploy(ZERO_ADDRESS, sender=deployer)


def test_initial_state(whitelist):
    assert whitelist.get_relays_amount() == 0
    assert whitelist.get_relays() is None, "must have 0 relays initially"
    assert whitelist.get_lido_dao_agent() == lido_dao_agent_address


def test_add_relay2(whitelist, lido_agent):
    receipt = whitelist.add_relay(*TEST_RELAY0, sender=lido_agent)
    assert_single_event(
        receipt, whitelist.RelayAdded, {"relay": TEST_RELAY0, "uri_hash": TEST_RELAY0_URI_HASH}
    )
    relays = whitelist.get_relays()
    assert relays == list(TEST_RELAY0)


@suppress_3rd_party_deprecation_warnings
def test_add_relay_with_same_uri(whitelist, lido_agent):
    whitelist.add_relay(*TEST_RELAY0, sender=lido_agent)
    with reverts("relay with the URI already exists"):
        whitelist.add_relay(*TEST_RELAY0, sender=lido_agent)


@suppress_3rd_party_deprecation_warnings
def test_add_too_many_relays(whitelist, lido_agent):
    test_relays = [list(Relay(f"uri #{i}", "", bool(i % 2), "")) for i in range(MAX_RELAYS_NUM)]

    for relay in test_relays:
        whitelist.add_relay(*relay, sender=lido_agent)

    for actual, expected in zip(whitelist.get_relays(), test_relays):
        assert list(actual) == expected

    with reverts():
        whitelist.add_relay(*TEST_RELAY0, sender=lido_agent)


@suppress_3rd_party_deprecation_warnings
def test_add_relay_with_empty_uri(whitelist, lido_agent):
    with reverts("relay URI must not be empty"):
        whitelist.add_relay(*Relay("", "", False, ""), sender=lido_agent)


@suppress_3rd_party_deprecation_warnings
def test_remove_relay_with_empty_uri(whitelist, lido_agent):
    with reverts("relay URI must not be empty"):
        whitelist.remove_relay("", sender=lido_agent)


@suppress_3rd_party_deprecation_warnings
def test_remove_relay_when_no_such_relays(whitelist, lido_agent):
    whitelist.add_relay(*TEST_RELAY0, sender=lido_agent)
    whitelist.add_relay(*TEST_RELAY1, sender=lido_agent)
    with reverts("no relay with the URI"):
        whitelist.remove_relay("non-presenting uri", sender=lido_agent)


@suppress_3rd_party_deprecation_warnings
def test_remove_relay_when_no_relays(whitelist, lido_agent):
    with reverts("no relay with the URI"):
        whitelist.remove_relay(TEST_RELAY0.uri, sender=lido_agent)


def test_remove_single_existing_relay(whitelist, lido_agent):
    whitelist.add_relay(*TEST_RELAY0, sender=lido_agent)
    receipt = whitelist.remove_relay(TEST_RELAY0.uri, sender=lido_agent)
    assert_single_event(
        receipt, whitelist.RelayRemoved, {"uri": TEST_RELAY0.uri, "uri_hash": TEST_RELAY0_URI_HASH}
    )


def test_remove_first_relay(whitelist, lido_agent):
    whitelist.add_relay(*TEST_RELAY0, sender=lido_agent)
    whitelist.add_relay(*TEST_RELAY1, sender=lido_agent)
    receipt = whitelist.remove_relay(TEST_RELAY0.uri, sender=lido_agent)
    assert_single_event(
        receipt, whitelist.RelayRemoved, {"uri": TEST_RELAY0.uri, "uri_hash": TEST_RELAY0_URI_HASH}
    )
    assert whitelist.get_relays() == list(TEST_RELAY1)


def test_remove_last_relay(whitelist, lido_agent):
    whitelist.add_relay(*TEST_RELAY0, sender=lido_agent)
    whitelist.add_relay(*TEST_RELAY1, sender=lido_agent)
    receipt = whitelist.remove_relay(TEST_RELAY1.uri, sender=lido_agent)
    assert_single_event(
        receipt, whitelist.RelayRemoved, {"uri": TEST_RELAY1.uri, "uri_hash": TEST_RELAY1_URI_HASH}
    )
    assert whitelist.get_relays() == list(TEST_RELAY0)


def test_remove_middle_relay(whitelist, lido_agent):
    test_relays = [list(Relay(f"uri #{i}", "", bool(i % 2), "")) for i in range(MAX_RELAYS_NUM)]

    for relay in test_relays:
        whitelist.add_relay(*relay, sender=lido_agent)

    whitelist.remove_relay("uri #7", sender=lido_agent)
    test_relays[7] = test_relays.pop()

    for actual, expected in zip(whitelist.get_relays(), test_relays):
        assert list(actual) == expected


@suppress_3rd_party_deprecation_warnings
def test_stranger_cannot_add_relay(whitelist, lido_agent, stranger):
    assert whitelist.get_lido_dao_agent() == lido_agent

    with reverts("not lido agent"):
        whitelist.add_relay(*TEST_RELAY0, sender=stranger)


@suppress_3rd_party_deprecation_warnings
def test_stranger_cannot_remove_relay(whitelist, lido_agent, stranger):
    assert whitelist.get_lido_dao_agent() == lido_agent

    with reverts("not lido agent"):
        whitelist.remove_relay("arbitrary uri", sender=stranger)
