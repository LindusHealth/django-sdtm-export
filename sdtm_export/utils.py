from datetime import date, datetime


def get_missing_node(cls, **kwargs):
    node = cls()
    node.is_missing_for_export = True
    for key, value in kwargs.items():
        setattr(node, key, value)
    # Prevent accidental saving of dummy instance
    node.save = lambda: None
    return node


def is_node_missing(node):
    return getattr(node, "is_missing_for_export", False)


def format_value(value):
    # Default to empty string rather than None
    if value is None:
        return ""

    # Convert to proper boolean format if response
    # resembles a boolean
    if value == "Yes" or value is True:
        return "Y"

    if value == "No" or value is False:
        return "N"

    if isinstance(value, date) or isinstance(value, datetime):
        return value.isoformat()

    return value
