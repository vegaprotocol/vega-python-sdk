from vega.pow import solve, count_zeros
from hashlib import sha3_256


def test_pow():
    block_hash = "2FB2146FC01F21D358323174BAA230E7DE61C0F150B7FBC415C896B0C23E50FF"
    tx_id = "2E7A16D9EF690F0D2BEED115FBA13BA2AAA16C8F971910AD88C72B9DB010C7D4"
    nonce = solve(block_hash, bytes(tx_id, "utf-8"), 2)

    assert nonce == 4


def test_pow_works():
    block_hash = "2FB2146FC01F21D358323174BAA230E7DE61C0F150B7FBC415C896B0C23E50FF"
    tx_id = bytes(
        "2E7A16D9EF690F0D2BEED115FBA13BA2AAA16C8F971910AD88C72B9DB010C7D4", "utf-8"
    )
    nonce = solve(block_hash, tx_id, 2)
    harder_nonce = solve(block_hash, tx_id, 3)

    byte_hash = bytes(block_hash, "utf-8")
    # Function to calculate proof of work
    assert (
        count_zeros(
            sha3_256(
                b"Vega_SPAM_PoW"
                + byte_hash
                + tx_id
                + nonce.to_bytes(8, byteorder="big")
            ).digest()
        )
        >= 2
    )
    assert (
        count_zeros(
            sha3_256(
                b"Vega_SPAM_PoW"
                + byte_hash
                + tx_id
                + harder_nonce.to_bytes(8, byteorder="big")
            ).digest()
        )
        >= 3
    )
