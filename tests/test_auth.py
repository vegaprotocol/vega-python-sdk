from vega.auth import Signer


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
        (
            "fancy basket install citizen purchase flush raven valid pottery short pony"
            " happy purchase dove rely obey dry slow action call unlock also foot clump"
        ),
        derivations=1,
    )
    assert (
        signer._pub_key
        == "af04195d9bdc08a9d709a3e5efa44e6e0e77dd539b64949e0a7dc6125b06a47b"
    )
    signer2 = Signer.from_mnemonic(
        (
            "swing ceiling chaos green put insane ripple desk match tip melt usual"
            " shrug turkey renew icon parade veteran lens govern path rough page render"
        ),
        derivations=1,
    )
    assert (
        signer2._pub_key
        == "b5fd9d3c4ad553cb3196303b6e6df7f484cf7f5331a572a45031239fd71ad8a0"
    )
    signer3 = Signer.from_mnemonic(
        "artist three verify stairs size burden flight topic entire used iron speed",
        derivations=1,
    )
    assert (
        signer3._pub_key
        == "3ed72396c7e79708b17d06ad067c3ecb93f2ee49999e5eb1f5b6c6d864bea4d9"
    )


def test_from_metamask_mnemonic():
    signer = Signer.from_mnemonic(
        "artist three verify stairs size burden flight topic entire used iron speed",
        derivations=0,
    )
    assert (
        signer._pub_key
        == "df450a94e233c6f6f4a705fac1e2c84ccaa76a9c6ae9c2799b80232497d62d85"
    )


def test_signature():
    signer = Signer.from_mnemonic(
        (
            "swing ceiling chaos green put insane ripple desk match tip melt usual"
            " shrug turkey renew icon parade veteran lens govern path rough page render"
        ),
        derivations=1,
    )
    signature = signer.sign(
        bytes("Je ne connaîtrai pas la peur car la peur tue l'esprit.", "utf-8")
    )

    assert (
        signature.hex()
        == "4ad1fcd911f18d0df24de692376e5beac2700322e2ab5083bcf59fd17e0a21ffd"
        + "64c88e4ba79162a7d46abd9ed0a81817c1648c8d7e93ed1b1d13499b12adb08"
    )
