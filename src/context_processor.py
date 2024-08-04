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
    return dict(is_active=is_active, is_disabled=is_disabled)
