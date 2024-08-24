from enum import Enum
from flask import Config, g, session
from gotrue import SyncSupportedStorage, VerifyTokenHashParams, EmailOtpType
from gotrue.errors import AuthApiError, AuthRetryableError
from supabase import create_client, Client
from supabase.client import ClientOptions
from typing import List, cast
from werkzeug.local import LocalProxy
import logging as log
import time


class SessionStorage(SyncSupportedStorage):
    """ Session storage for storing authentication client information, used by the Supabase client library. """

    def __init__(self):
        self.storage = session

    def get_item(self, key: str) -> str | None:
        if key in self.storage:
            return self.storage[key]

    def set_item(self, key: str, value: str) -> None:
        self.storage[key] = value

    def remove_item(self, key: str) -> None:
        if key in self.storage:
            self.storage.pop(key, None)


class AuthResult(Enum):
    """ Represents the result of processing functions of an authentication client. """
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    CONFIRM_EMAIL = "confirm_email"


class AssuranceLevel(Enum):
    """ Represents the Authentication Assurance Level (AAL). """
    ONE = "aal1"
    TWO = "aal2"


class AuthUserInfo:
    """ Represents the information of an authenticated user. """

    def __init__(self, id: str, aal_current: str, aal_next: str):
        self.id = id
        self.aal_current = aal_current
        self.aal_next = aal_next
        self.factors: List[AuthUserFactorInfo] = []


class AuthSignUpInfo:
    """ Represents the sing-up information of an user. """

    def __init__(self, id: str):
        self.id = id


class AuthUserFactorInfo:
    """ Represents the factor information of an authenticated user. """

    def __init__(self, id: str, name: str, type: str):
        self.id = id
        self.name = name
        self.type = type


class AuthSessionInfo:
    """ Represents the session information of an authenticated user. """

    def __init__(self, access_token: str, refresh_token):
        self.access_token = access_token
        self.refresh_token: str = refresh_token


class FactorInfo:
    """ Represents the information of an enrolled factor. """

    def __init__(self, id: str, qr_code: str, secret: str, uri: str):
        self.id = id
        self.qr_code = qr_code
        self.secret = secret
        self.uri = uri


class ChallengeInfo:
    """ Represents the challenge information for a factor. """

    def __init__(self, id: str):
        self.id = id


class AuthClient:
    """ The AuthClient performs authentication client for Supabase services. """

    def __init__(self, logger: log.Logger, config: Config):
        self.logger = logger
        self.config = config

    def get_auth_client(self):
        """ Retrieves the authentication client. """
        return cast(Client, LocalProxy(self.__get_supabase))

    def __get_supabase(self):
        """ Retrieves the Supabase client. """
        url = self.config["SUPABASE"]["SUPABASE_URL"]
        key = self.config["SUPABASE"]["SUPABASE_KEY"]
        options = ClientOptions(storage=SessionStorage(), flow_type="pkce")
        if "supabase" not in g:
            g.supabase = Client(url, key, options)
        return g.supabase

    def verify_otp(self, token_hash: str, type: EmailOtpType) -> AuthResult:
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.verify_otp(VerifyTokenHashParams(token_hash=token_hash, type=type))
                if not response:
                    return AuthResult.FAILURE
                return AuthResult.SUCCESS
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status == 400:
                    return AuthResult.FAILURE
                else:
                    self.logger.exception(msg=e.message)
                    return AuthResult.ERROR
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return AuthResult.UNAVAILABLE

    def get_session(self) -> tuple[AuthResult, AuthSessionInfo | None]:
        """
        Retrieves the current session information.
        If a cache exists in the request scope, the information is retrieved from the cache.
        """
        cached_data = g.get("supabase_get_session", None)
        if cached_data:
            return (AuthResult.SUCCESS, cast(AuthSessionInfo, cached_data))
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.get_session()
                if not response:
                    return (AuthResult.FAILURE, None)
                assert response is not None
                session_info = AuthSessionInfo(
                    response.access_token,
                    response.refresh_token)
                g.supabase_get_session = session_info
                return (AuthResult.SUCCESS, session_info)
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status == 400:
                    return (AuthResult.FAILURE, None)
                else:
                    self.logger.exception(msg=e.message)
                    return (AuthResult.ERROR, None)
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return (AuthResult.UNAVAILABLE, None)

    def exchange_code_for_session(self, code: str) -> tuple[AuthResult, AuthUserInfo | None, AuthSessionInfo | None]:
        """
        Sing-in an existing user by exchanging an Auth Code issued during the PKCE flow.
        """
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.exchange_code_for_session({"auth_code": code})  # type: ignore
                if not response:
                    return (AuthResult.FAILURE, None, None)
                mfa_response = supabase.auth.mfa.get_authenticator_assurance_level()
                assert response.user is not None
                assert response.session is not None
                assert mfa_response.current_level is not None
                assert mfa_response.next_level is not None
                user_info = AuthUserInfo(
                    response.user.id,
                    mfa_response.current_level,
                    mfa_response.next_level)
                session_info = AuthSessionInfo(
                    response.session.access_token,
                    response.session.refresh_token)
                return (AuthResult.SUCCESS, user_info, session_info)
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status == 400:
                    return (AuthResult.FAILURE, None, None)
                else:
                    self.logger.exception(msg=e.message)
                    return (AuthResult.ERROR, None, None)
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return (AuthResult.UNAVAILABLE, None, None)

    def get_user(self) -> tuple[AuthResult, AuthUserInfo | None]:
        """
        Retrieves the current authenticated user's information.
        If a cache exists in the request scope, the information is retrieved from the cache.
        """
        cached_data = g.get("supabase_get_user", None)
        if cached_data:
            return (AuthResult.SUCCESS, cast(AuthUserInfo, cached_data))

        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.get_user()
                if not response:
                    return (AuthResult.FAILURE, None)
                mfa_response = supabase.auth.mfa.get_authenticator_assurance_level()
                assert response is not None
                assert mfa_response.current_level is not None
                assert mfa_response.next_level is not None
                user_info = AuthUserInfo(
                    response.user.id,
                    mfa_response.current_level,
                    mfa_response.next_level)

                if response.user.factors:
                    response.user.factors.sort(
                        key=lambda factor: factor.created_at)
                    for factor in response.user.factors:
                        if factor.status == "unverified":
                            continue
                        assert factor.friendly_name is not None
                        factor_info = AuthUserFactorInfo(
                            factor.id,
                            factor.friendly_name,
                            factor.factor_type)
                        user_info.factors.append(factor_info)

                g.supabase_get_user = user_info
                return (AuthResult.SUCCESS, user_info)
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.message.startswith("Invalid Refresh Token"):
                    return (AuthResult.TIMEOUT, None)
                elif e.status == 400:
                    return (AuthResult.FAILURE, None)
                else:
                    self.logger.exception(msg=e.message)
                    return (AuthResult.ERROR, None)
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return (AuthResult.UNAVAILABLE, None)

    def sign_up(self, email: str, password: str) -> tuple[AuthResult, AuthSignUpInfo | None]:
        """ Executes user sign-up. """
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.sign_up({"email": email, "password": password})
                assert response.user is not None
                signup_info = AuthSignUpInfo(response.user.id)

                if response.session is None:
                    return (AuthResult.CONFIRM_EMAIL, signup_info)
                else:
                    return (AuthResult.SUCCESS, signup_info)

            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status == 400:
                    return (AuthResult.FAILURE, None)
                else:
                    self.logger.exception(msg=e.message)
                    return (AuthResult.ERROR, None)
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return (AuthResult.UNAVAILABLE, None)

    def sign_in_with_oauth(self, provider: str, redirect_to: str) -> tuple[AuthResult, str | None]:
        """ Authenticates using an oauth. """
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.sign_in_with_oauth({"provider": provider, "options": {"redirect_to": redirect_to}})
                return (AuthResult.SUCCESS, response.url)
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status == 400:
                    return (AuthResult.FAILURE, None)
                else:
                    self.logger.exception(msg=e.message)
                    return (AuthResult.ERROR, None)
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return (AuthResult.UNAVAILABLE, None)

    def sign_in_with_password(self, email: str, password: str) -> tuple[AuthResult, AuthUserInfo | None, AuthSessionInfo | None]:
        """ Authenticates using an email and password. """
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                mfa_response = supabase.auth.mfa.get_authenticator_assurance_level()
                assert response.user is not None
                assert response.session is not None
                assert mfa_response.current_level is not None
                assert mfa_response.next_level is not None
                user_info = AuthUserInfo(
                    response.user.id,
                    mfa_response.current_level,
                    mfa_response.next_level)
                session_info = AuthSessionInfo(
                    response.session.access_token,
                    response.session.refresh_token)
                return (AuthResult.SUCCESS, user_info, session_info)
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status == 400:
                    return (AuthResult.FAILURE, None, None)
                else:
                    self.logger.exception(msg=e.message)
                    return (AuthResult.ERROR, None, None)
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return (AuthResult.UNAVAILABLE, None, None)

    def enroll(self, friendly_name: str) -> tuple[AuthResult, FactorInfo | None]:
        """ Enrolls a new factor. """
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.mfa.enroll({
                    "factor_type": "totp",
                    "friendly_name": friendly_name})
                factor_info = FactorInfo(
                    response.id,
                    response.totp.qr_code,
                    response.totp.secret,
                    response.totp.uri)
                return (AuthResult.SUCCESS, factor_info)
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status == 400:
                    return (AuthResult.FAILURE, None)
                else:
                    self.logger.exception(msg=e.message)
                    return (AuthResult.ERROR, None)
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return (AuthResult.UNAVAILABLE, None)

    def challenge(self, factor_id: str) -> tuple[AuthResult, ChallengeInfo | None]:
        """ Creates a challenge for a factor. """
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.mfa.challenge(
                    {"factor_id": factor_id})
                challenge_info = ChallengeInfo(response.id)
                return (AuthResult.SUCCESS, challenge_info)
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status == 400:
                    return (AuthResult.FAILURE, None)
                else:
                    self.logger.exception(msg=e.message)
                    return (AuthResult.ERROR, None)
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return (AuthResult.UNAVAILABLE, None)

    def verify(self, factor_id: str, challenge_id: str, code: str) -> tuple[AuthResult, AuthUserInfo | None]:
        """ Verifies a challenge for a factor. """
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.mfa.verify({
                    "factor_id": factor_id,
                    "challenge_id": challenge_id,
                    "code": code
                })
                mfa_response = supabase.auth.mfa.get_authenticator_assurance_level()
                assert response.user is not None
                assert mfa_response.current_level is not None
                assert mfa_response.next_level is not None
                user_info = AuthUserInfo(
                    response.user.id,
                    mfa_response.current_level,
                    mfa_response.next_level)
                return (AuthResult.SUCCESS, user_info)
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status == 400 or e.status == 422:
                    return (AuthResult.FAILURE, None)
                else:
                    self.logger.exception(msg=e.message)
                    return (AuthResult.ERROR, None)
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return (AuthResult.UNAVAILABLE, None)

    def reset_password(self, email: str) -> AuthResult:
        """ Resets the user's password. """
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                supabase.auth.reset_password_email(email)
                return AuthResult.SUCCESS
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status == 400:
                    return AuthResult.FAILURE
                else:
                    self.logger.exception(msg=e.message)
                    return AuthResult.ERROR
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return AuthResult.UNAVAILABLE

    def update_password(self, password: str) -> AuthResult:
        """ Updates the user's password. """
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = supabase.auth.update_user({"password": password})
                return AuthResult.SUCCESS
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                if e.status >= 400 and e.status < 500:
                    return AuthResult.FAILURE
                else:
                    self.logger.exception(msg=e.message)
                    return AuthResult.ERROR
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return AuthResult.UNAVAILABLE

    def sign_out(self) -> AuthResult:
        """ Executes user sign-out. """
        supabase = self.get_auth_client()
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                supabase.auth.sign_out()
                return AuthResult.SUCCESS
            except AuthRetryableError as e:
                self.logger.warn(f"Attempt {attempt + 1} failed with retryable error: {e}")
                time.sleep(2 ** attempt)
            except AuthApiError as e:
                self.logger.exception(msg=e.message)
                return AuthResult.ERROR
        self.logger.error("Operation failed after several attempts. Please check your Supabase service.")
        return AuthResult.UNAVAILABLE
