import socket
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import grpc
import pytest

import vegawallet.proto.vega.api.v1.core_pb2 as core_proto
import vegawallet.proto.vega.commands.v1.commands_pb2 as commands_proto
from vegawallet.client import Client
from vegawallet.proto.data_node.api.v2.trading_data_pb2_grpc import (
    TradingDataServiceServicer as TradingDataServiceServicerV2,
)
from vegawallet.proto.data_node.api.v2.trading_data_pb2_grpc import (
    add_TradingDataServiceServicer_to_server as add_TradingDataServiceServicer_v2_to_server,
)
from vegawallet.proto.vega.api.v1.core_pb2_grpc import (
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

    def LastBlockHeight(self, request):
        return core_proto.LastBlockHeightResponse(height=245)

    def SubmitTransaction(self, request):
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
    )
    assert (
        client._signer._pub_key
        == "af04195d9bdc08a9d709a3e5efa44e6e0e77dd539b64949e0a7dc6125b06a47b"
    )

    client.submit_transaction(
        commands_proto.BatchMarketInstructions(), "batch_market_instructions"
    )
