from vega.pow import solve


def test_pow():
    block_hash = "2FB2146FC01F21D358323174BAA230E7DE61C0F150B7FBC415C896B0C23E50FF"
    tx_id = "2E7A16D9EF690F0D2BEED115FBA13BA2AAA16C8F971910AD88C72B9DB010C7D4"
    nonce = solve(block_hash, bytes(tx_id, "utf-8"), 2)

    assert nonce == 4
