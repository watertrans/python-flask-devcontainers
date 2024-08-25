from clients import AssuranceLevel, AuthClient, AuthResult
from flask import redirect, url_for, request
from functools import wraps
import inject


def signin_required(level: AssuranceLevel):
    def decorator(f):
        @wraps(f)
        @inject.autoparams("auth_client")
        def decorated(*args, auth_client: AuthClient, **kwargs):
            result, user_info = auth_client.get_user()
            if result == AuthResult.SUCCESS:
                assert user_info is not None
                if level.value == AssuranceLevel.TWO.value and user_info.aal_current == AssuranceLevel.ONE.value:
                    return redirect(url_for("auth.verify", redirect_to=request.path))
            elif result == AuthResult.TIMEOUT:
                return redirect(url_for("auth.signin", redirect_to=request.path))
            elif result == AuthResult.UNAVAILABLE:
                return redirect(url_for("errors.service_unavailable"))
            elif result == AuthResult.FAILURE:
                return redirect(url_for("auth.signin", redirect_to=request.path))
            return f(*args, **kwargs)
        return decorated
    return decorator
