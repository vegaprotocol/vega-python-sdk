import random
import grpc
import uuid
from typing import Any

import vegawallet.proto.vega.api.v1.core_pb2 as core_proto
import vegawallet.proto.vega.commands.v1.signature_pb2 as signature_proto
import vegawallet.proto.vega.commands.v1.transaction_pb2 as transaction_proto
from vegawallet.auth import Signer
from vegawallet.pow import solve
from vegawallet.grpc.client import VegaCoreClient, VegaTradingDataClient


class TransactionFailureError(Exception):
    pass


class Client:
    def __init__(self, mnemonic: str, grpc_url: str) -> None:
        self._signer = Signer.from_mnemonic(mnemonic=mnemonic)

        self.grpc_url = grpc_url

        self._trading_data_client = VegaTradingDataClient(
            self.grpc_url,
            channel=self._new_channel(),
        )
        self._core_data_client = VegaCoreClient(
            self.grpc_url,
            channel=self._new_channel(),
        )

    def _new_channel(self):
        channel = grpc.insecure_channel(
            self.grpc_url,
            options=(
                ("grpc.enable_http_proxy", 0),
                ("grpc.max_send_message_length", 1024 * 1024 * 20),
                ("grpc.max_receive_message_length", 1024 * 1024 * 20),
            ),
        )
        grpc.channel_ready_future(channel).result(timeout=30)
        return channel

    def _sign_tx(
        self, serialised_input_data: bytes, chain_id: bytes
    ) -> signature_proto.Signature:
        return signature_proto.Signature(
            value=self._signer.sign(
                to_sign=chain_id + int(0).to_bytes() + serialised_input_data
            ).hex(),
            algo="vega/ed25519",
            version=1,
        )

    def _calc_pow(
        self, block_hash: str, difficulty: int
    ) -> transaction_proto.ProofOfWork:
        tx_id = bytes(uuid.uuid4().hex, "utf-8")
        return transaction_proto.ProofOfWork(
            tid=tx_id.decode(),
            nonce=solve(block_hash=block_hash, tx_id=tx_id, difficulty=difficulty),
        )

    def sign_transaction(
        self,
        transaction: Any,
        transaction_type: str,
    ) -> core_proto.SubmitTransactionResponse:
        res = self._core_data_client.LastBlockHeight(
            core_proto.LastBlockHeightRequest()
        )

        transaction_info = {transaction_type: transaction}
        input_data = transaction_proto.InputData(
            nonce=self._get_nonce(), block_height=res.height, **transaction_info
        )

        serialised = input_data.SerializeToString()

        return transaction_proto.Transaction(
            input_data=serialised,
            signature=self._sign_tx(
                serialised_input_data=serialised, chain_id=bytes(res.chain_id, "utf-8")
            ),
            pub_key=self._signer._pub_key,
            version=3,
            pow=self._calc_pow(block_hash=res.hash, difficulty=res.spam_pow_difficulty),
        )

    def submit_transaction(
        self,
        transaction: Any,
        transaction_type: str,
    ) -> core_proto.SubmitTransactionResponse:
        signed_tx = self.sign_transaction(
            transaction=transaction, transaction_type=transaction_type
        )

        return self._core_data_client.SubmitTransaction(signed_tx)

    def _get_nonce(self) -> int:
        return random.randint(1, 1e10)
