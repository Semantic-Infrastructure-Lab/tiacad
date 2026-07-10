"""Parser-specific error types."""

from ..utils.exceptions import TiaCADError


class TiaCADParserError(TiaCADError):
    """Error during YAML parsing."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
