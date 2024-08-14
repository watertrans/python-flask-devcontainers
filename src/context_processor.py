from flask import session


def utility_processor():
    """ Define custom functions available in the template. """
    def is_active(expression: bool) -> str:
        """ If the expression is true, return active. """
        if expression:
            return "active"
        else:
            return ""

    def is_disabled(expression: bool) -> str:
        """ If the expression is true, return disabled. """
        if expression:
            return "disabled"
        else:
            return ""

    def is_valid(expression: bool) -> str:
        """ If the expression is true, return is-valid. """
        if expression:
            return "is-valid"
        else:
            return ""

    def is_invalid(expression: bool) -> str:
        """ If the expression is true, return is-invalid. """
        if expression:
            return "is-invalid"
        else:
            return ""

    def is_checked(expression: bool) -> str:
        """ If the expression is true, return checked. """
        if expression:
            return "checked"
        else:
            return ""

    def is_signedin() -> bool:
        """ If singed in, return True. """
        return session.get("user_id", None)

    return dict(is_active=is_active,
                is_disabled=is_disabled,
                is_valid=is_valid,
                is_invalid=is_invalid,
                is_checked=is_checked,
                is_signedin=is_signedin)
