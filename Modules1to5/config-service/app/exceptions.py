"""
app/exceptions.py
-----------------
Domain exceptions mapped to HTTP responses in main.py.
"""


class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, id: str):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} '{id}' not found")


class DuplicateNameError(Exception):
    """Raised when a unique name constraint would be violated."""

    def __init__(self, resource: str, name: str):
        self.resource = resource
        self.name = name
        super().__init__(f"{resource} with name '{name}' already exists")
