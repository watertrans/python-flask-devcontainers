from clients import AssuranceLevel, AuthClient, AuthResult
from flask import Config
import logging as log


class AuthService:
    """ The AuthService performs authentication for this application. """

    def __init__(self, logger: log.Logger, config: Config, auth_client: AuthClient):
        self.logger = logger
        self.config = config
        self.auth_client = auth_client

    def has_factor(self):
        """ Returns whether the current user has the factor. """
        result, user_info = self.auth_client.get_user()
        if result == AuthResult.SUCCESS:
            assert user_info is not None
            if user_info.aal_current == AssuranceLevel.TWO.value or user_info.aal_next == AssuranceLevel.TWO.value:
                return True
        return False

    def is_two_factor_verified(self):
        """ Returns whether the current user has completed two-factor authentication. """
        result, user_info = self.auth_client.get_user()
        if result == AuthResult.SUCCESS:
            assert user_info is not None
            if user_info.aal_current == AssuranceLevel.TWO.value:
                return True
        return False

    def verify_token_hash_for_recovery(self, token_hash: str):
        return self.auth_client.verify_otp(token_hash, "recovery")

    def get_session(self):
        """ Retrieves the current session. """
        return self.auth_client.get_session()

    def get_user(self):
        """ Retrieves the current authenticated user's information. """
        return self.auth_client.get_user()

    def sign_up(self, email: str, password: str):
        """ Executes user sign-up. """
        return self.auth_client.sign_up(email, password)

    def auth(self, email: str, password: str):
        """ Authenticates using an email and password. """
        return self.auth_client.auth(email, password)

    def enroll(self, friendly_name: str):
        """ Enrolls a new factor. """
        return self.auth_client.enroll(friendly_name)

    def challenge(self, factor_id: str):
        """ Creates a challenge for a factor. """
        return self.auth_client.challenge(factor_id)

    def verify(self, factor_id: str, challenge_id: str, code: str):
        """ Verifies a challenge for a factor. """
        return self.auth_client.verify(factor_id, challenge_id, code)

    def reset_password(self, email: str):
        """ Resets the user's password. """
        return self.auth_client.reset_password(email)

    def update_password(self, password: str):
        """ Updates the user's password. """
        return self.auth_client.update_password(password)

    def sign_out(self):
        """ Executes user sign-out. """
        return self.auth_client.sign_out()
