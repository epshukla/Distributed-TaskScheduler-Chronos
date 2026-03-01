class ChronosError(Exception):
    """Base exception for all Chronos errors."""

    def __init__(self, message: str = "An error occurred", error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
