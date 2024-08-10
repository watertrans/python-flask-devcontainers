from clients import AuthClient
from flask import Config


class AuthService:
    """The AuthService performs authentication for this application."""

    def __init__(self, config: Config, auth_client: AuthClient):
        self.config = config
        self.auth_client = auth_client

    def auth(self, email: str, password: str):
        return self.auth_client.auth_supabase(email, password)
