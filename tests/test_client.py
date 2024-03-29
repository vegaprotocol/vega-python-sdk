import socket
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import grpc
import pytest
from hashlib import sha3_256

import vega.proto.vega.api.v1.core_pb2 as core_proto
import vega.proto.vega.commands.v1.commands_pb2 as commands_proto
from vega.client import Client
from vega.proto.data_node.api.v2.trading_data_pb2_grpc import (
    TradingDataServiceServicer as TradingDataServiceServicerV2,
)
from vega.pow import solve, count_zeros


from vega.proto.data_node.api.v2.trading_data_pb2_grpc import (
    add_TradingDataServiceServicer_to_server as add_TradingDataServiceServicer_v2_to_server,
)
from vega.proto.vega.api.v1.core_pb2_grpc import (
    CoreServiceServicer,
    add_CoreServiceServicer_to_server,
)


@pytest.fixture
def servicers_and_port():
    server = grpc.server(ThreadPoolExecutor(1))
    port = find_free_port()
    server.add_insecure_port(f"[::]:{port}")
    server.start()

    class MockCoreServicer(CoreServiceServicer):
        pass

    class MockTradingDataServicer(TradingDataServiceServicerV2):
        pass

    return server, port, MockCoreServicer, MockTradingDataServicer


def find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        ret_sock = s.getsockname()[1]
    return ret_sock


def test_basic_signing(servicers_and_port):
    server, port, core_servicer, trading_data_servicer = servicers_and_port

    def LastBlockHeight(request, context):
        return core_proto.LastBlockHeightResponse(
            height=245,
            hash="2FB2146FC01F21D358323174BAA230E7DE61C0F150B7FBC415C896B0C23E50FF",
            chain_id="4",
            spam_pow_difficulty=1,
            spam_pow_number_of_past_blocks=100,
            spam_pow_number_of_tx_per_block=100,
        )

    def SubmitTransaction(request, context):
        return core_proto.SubmitTransactionResponse(success=True)

    core_servicer.LastBlockHeight = LastBlockHeight
    core_servicer.SubmitTransaction = SubmitTransaction

    add_TradingDataServiceServicer_v2_to_server(trading_data_servicer, server)
    add_CoreServiceServicer_to_server(core_servicer, server)

    client = Client(
        mnemonic=(
            "fancy basket install citizen purchase flush raven valid pottery short pony"
            " happy purchase dove rely obey dry slow action call unlock also foot clump"
        ),
        grpc_url=f"localhost:{port}",
        derivations=1,
    )
    assert (
        client._signer._pub_key
        == "af04195d9bdc08a9d709a3e5efa44e6e0e77dd539b64949e0a7dc6125b06a47b"
    )

    client.submit_transaction(
        commands_proto.BatchMarketInstructions(), "batch_market_instructions"
    )


def test_client_pubkey(servicers_and_port):
    server, port, core_servicer, trading_data_servicer = servicers_and_port

    def LastBlockHeight(request, context):
        return core_proto.LastBlockHeightResponse(
            height=245,
            hash="2FB2146FC01F21D358323174BAA230E7DE61C0F150B7FBC415C896B0C23E50FF",
            chain_id="4",
            spam_pow_difficulty=1,
            spam_pow_number_of_past_blocks=100,
            spam_pow_number_of_tx_per_block=100,
        )

    core_servicer.LastBlockHeight = LastBlockHeight

    add_TradingDataServiceServicer_v2_to_server(trading_data_servicer, server)
    add_CoreServiceServicer_to_server(core_servicer, server)
    client = Client(
        mnemonic=(
            "fancy basket install citizen purchase flush raven valid pottery short pony"
            " happy purchase dove rely obey dry slow action call unlock also foot clump"
        ),
        grpc_url=f"localhost:{port}",
        derivations=1,
    )
    assert (
        client._signer._pub_key
        == "af04195d9bdc08a9d709a3e5efa44e6e0e77dd539b64949e0a7dc6125b06a47b"
    )


def test_client_pow(servicers_and_port):
    server, port, core_servicer, trading_data_servicer = servicers_and_port

    def LastBlockHeight(request, context):
        return core_proto.LastBlockHeightResponse(
            height=245,
            hash="2FB2146FC01F21D358323174BAA230E7DE61C0F150B7FBC415C896B0C23E50FF",
            chain_id="4",
            spam_pow_difficulty=1,
            spam_pow_number_of_past_blocks=100,
            spam_pow_number_of_tx_per_block=100,
        )

    core_servicer.LastBlockHeight = LastBlockHeight

    add_TradingDataServiceServicer_v2_to_server(trading_data_servicer, server)
    add_CoreServiceServicer_to_server(core_servicer, server)
    client = Client(
        mnemonic=(
            "fancy basket install citizen purchase flush raven valid pottery short pony"
            " happy purchase dove rely obey dry slow action call unlock also foot clump"
        ),
        grpc_url=f"localhost:{port}",
        derivations=1,
    )

    block_height = 245
    block_hash = "2FB2146FC01F21D358323174BAA230E7DE61C0F150B7FBC415C896B0C23E50FF"

    pow, _ = client._calc_pow(
        block_hash=block_hash,
        difficulty=2,
        block_height=block_height,
        num_past_blocks=1,
        num_tx_per_block=2,
        max_historic_blocks_buffer=0,
    )
    assert (
        count_zeros(
            sha3_256(
                b"Vega_SPAM_PoW"
                + bytes(block_hash, "utf-8")
                + bytes(pow.tid, "utf-8")
                + pow.nonce.to_bytes(8, byteorder="big")
            ).digest()
        )
        >= 2
    )

    pow2, _ = client._calc_pow(
        block_hash=block_hash,
        difficulty=2,
        block_height=block_height,
        num_past_blocks=1,
        num_tx_per_block=2,
        max_historic_blocks_buffer=0,
    )
    assert (
        count_zeros(
            sha3_256(
                b"Vega_SPAM_PoW"
                + bytes(block_hash, "utf-8")
                + bytes(pow2.tid, "utf-8")
                + pow2.nonce.to_bytes(8, byteorder="big")
            ).digest()
        )
        >= 2
    )

    pow3, _ = client._calc_pow(
        block_hash=block_hash,
        difficulty=2,
        block_height=block_height,
        num_past_blocks=1,
        num_tx_per_block=2,
        max_historic_blocks_buffer=0,
    )
    assert (
        count_zeros(
            sha3_256(
                b"Vega_SPAM_PoW"
                + bytes(block_hash, "utf-8")
                + bytes(pow3.tid, "utf-8")
                + pow3.nonce.to_bytes(8, byteorder="big")
            ).digest()
        )
        >= 3
    )
