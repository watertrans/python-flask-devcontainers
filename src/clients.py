from flask import Config


class AuthClient:
    """The AuthClient performs authentication client for other services."""

    def __init__(self, config: Config):
        self.config = config

    def auth_supabase(self, email: str, password: str):
        if email == "test" and password == "test":
            return True
        else:
            return False
