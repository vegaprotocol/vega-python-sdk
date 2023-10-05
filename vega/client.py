import random
import grpc
import uuid
from typing import Any

import vega.proto.vega.api.v1.core_pb2 as core_proto
import vega.proto.vega.commands.v1.signature_pb2 as signature_proto
import vega.proto.vega.commands.v1.transaction_pb2 as transaction_proto
from vega.auth import Signer
from vega.pow import solve
from vega.grpc.client import VegaCoreClient, VegaTradingDataClient


class TransactionFailureError(Exception):
    pass


class NoAvailablePoWBlockError(Exception):
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

        self._pow_blocks_used = {}
        self._block_hashes = {}

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
        self,
        block_hash: str,
        difficulty: int,
        block_height: int,
        num_past_blocks: int,
        num_tx_per_block: int,
    ) -> transaction_proto.ProofOfWork:
        tx_id = bytes(uuid.uuid4().hex, "utf-8")
        min_block = block_height - num_past_blocks + 1

        to_del_blocks = [
            historic_block
            for historic_block in self._pow_blocks_used.keys()
            if historic_block < min_block
        ]
        for block in to_del_blocks:
            del self._pow_blocks_used[block]
            del self._block_hashes[block]
        self._block_hashes[block_height] = block_hash

        block_height_to_use = block_height
        while (
            self._pow_blocks_used.setdefault(block_height_to_use, 0) >= num_tx_per_block
        ):
            block_height_to_use -= 1
        if (
            block_height_to_use < min_block
            or block_height_to_use not in self._block_hashes
        ):
            # When increasing difficulty is enabled we can do more per block by doing more PoW
            # but as first cut this will avoid bans
            raise NoAvailablePoWBlockError(
                "All seen blocks for PoW have been used. Sending a tx now would result"
                " in a ban, so wait for more blocks to be produced. "
            )
        self._pow_blocks_used[block_height_to_use] += 1

        return transaction_proto.ProofOfWork(
            tid=tx_id.decode(),
            nonce=solve(
                block_hash=self._block_hashes[block_height_to_use],
                tx_id=tx_id,
                difficulty=difficulty,
            ),
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
            pow=self._calc_pow(
                block_hash=res.hash,
                difficulty=res.spam_pow_difficulty,
                block_height=res.height,
                num_past_blocks=res.spam_pow_number_of_past_blocks,
                num_tx_per_block=res.spam_pow_number_of_tx_per_block,
            ),
        )

    def submit_transaction(
        self,
        transaction: Any,
        transaction_type: str,
    ) -> core_proto.SubmitTransactionResponse:
        signed_tx = self.sign_transaction(
            transaction=transaction, transaction_type=transaction_type
        )

        return self._core_data_client.SubmitTransaction(
            core_proto.SubmitTransactionRequest(
                tx=signed_tx, type=core_proto.SubmitTransactionRequest.Type.TYPE_SYNC
            )
        )

    def _get_nonce(self) -> int:
        return random.randint(1, int(1e10))
