import json
from typing import Dict, Union

# Example of WalletData in JSON format:
# {
#   123456789: {
#     "nickname": "JohnDoe",
#     "balance": 150.0
#   },
#   987654321: {
#     "nickname": "JaneDoe",
#     "balance": 200.5
#   }
# }
WalletData = Dict[int, Dict[str, Union[str, float]]]

SAVEFILE_NAME = "seremcoin_wallets.txt"

class SeremCoinWalletManager:
    def __init__(self):
        self.wallets: WalletData = {}

    def create_wallet(self, user_id: int, nickname: str) -> bool:
        """
        Create a new wallet for a user with the given user ID and nickname.
        Returns True if the wallet is created successfully, otherwise False.
        """
        if user_id not in self.wallets:
            self.wallets[user_id] = {"nickname": nickname, "balance": 0}
            return True
        return False

    def get_balance(self, user_id: int) -> Union[float, None]:
        """
        Return the balance of the user with the given user ID.
        Returns None if the user doesn't have a wallet.
        """
        if user_id in self.wallets:
            return self.wallets[user_id]["balance"]
        return None

    def add_seremcoins(self, user_id: int, amount: float) -> bool:
        """
        Add the specified amount of SeremCoins to the user with the given user ID.
        Returns True if the operation is successful, otherwise False.
        """
        if user_id in self.wallets:
            self.wallets[user_id]["balance"] += amount
            return True
        return False

    def _load_wallets(self, filename: str) -> bool:
        """
        Load the wallet data from the specified file.
        Returns True if the operation is successful, otherwise False.
        """
        try:
            with open(filename, "r") as f:
                self.wallets = json.load(f)
                return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def _save_wallets(self, filename: str) -> bool:
        """
        Save the wallet data to the specified file.
        Returns True if the operation is successful, otherwise False.
        """
        try:
            with open(filename, "w") as f:
                json.dump(self.wallets, f)
                return True
        except IOError:
            return False

    def __del__(self):
        """
        Destructor to save the wallet data to a file when the instance is deleted.
        """
        self._save_wallets(SAVEFILE_NAME)
