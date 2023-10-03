from vegawallet.auth import Signer


def test_from_pkey():
    signer = Signer.from_private_key(
        "ed752aca8c25d9832ba4b4c42ccf8d669e46cbb2fb8ff1ef2f71db9d5b081419"
    )
    assert (
        signer._pub_key
        == "af04195d9bdc08a9d709a3e5efa44e6e0e77dd539b64949e0a7dc6125b06a47b"
    )


def test_from_mnemonic():
    signer = Signer.from_mnemonic(
        "fancy basket install citizen purchase flush raven valid pottery short pony"
        " happy purchase dove rely obey dry slow action call unlock also foot clump"
    )
    assert (
        signer._pub_key
        == "af04195d9bdc08a9d709a3e5efa44e6e0e77dd539b64949e0a7dc6125b06a47b"
    )


def test_signature():
    signer = Signer.from_mnemonic(
        "swing ceiling chaos green put insane ripple desk match tip melt usual shrug"
        " turkey renew icon parade veteran lens govern path rough page render"
    )
    signature = signer.sign(
        bytes("Je ne connaîtrai pas la peur car la peur tue l'esprit.", "utf-8")
    )

    assert (
        signature.hex()
        == "4ad1fcd911f18d0df24de692376e5beac2700322e2ab5083bcf59fd17e0a21ffd"
        + "64c88e4ba79162a7d46abd9ed0a81817c1648c8d7e93ed1b1d13499b12adb08"
    )
