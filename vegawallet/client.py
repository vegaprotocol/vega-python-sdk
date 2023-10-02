from vegawallet.auth import Signer


class Client:
    def __init__(self, mnemonic: str) -> None:
        self._signer = Signer.from_mnemonic(mnemonic=mnemonic)

    def send_transaction(self, name: str, data) -> None:
        pass
