import socket
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import grpc
import pytest

import json
import vega.proto.vega.api.v1.core_pb2 as core_proto
import vega.proto.vega.commands.v1.commands_pb2 as commands_proto
import vega.proto.vega.vega_pb2 as vega_proto
from vega.client import Client, transaction_to_json
from vega.proto.data_node.api.v2.trading_data_pb2_grpc import (
    TradingDataServiceServicer as TradingDataServiceServicerV2,
)
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
    _, port, _, _ = servicers_and_port

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


def test_transaction_to_json():
    order = commands_proto.OrderSubmission(
        market_id="69abf5c456c20f4d189cea79a11dfd6b0958ead58ab34bd66f73eea48aee600c",
        price="1",
        size=1,
        side=vega_proto.Side.SIDE_BUY,
        time_in_force=vega_proto.Order.TimeInForce.TIME_IN_FORCE_GTC,
        type=vega_proto.Order.Type.TYPE_LIMIT,
    )
    js = transaction_to_json(order)

    assert js == {
        "tx": "CkA2OWFiZjVjNDU2YzIwZjRkMTg5Y2VhNzlhMTFkZmQ2YjA5NThlYWQ1OGFiMzRiZDY2ZjczZWVhNDhhZWU2MDBjEgExGAEgASgBOAE=",
        "type": "TYPE_SYNC",
    }
