def utility_processor():
    """ Define custom functions available in the template. """
    def is_active(expression: bool) -> str:
        """ If the expression is true, return active. """
        if expression:
            return "active"
        else:
            return ""
    return dict(is_active=is_active)
