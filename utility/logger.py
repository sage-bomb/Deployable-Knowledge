"""Simple logging setup for the application.

The project previously relied heavily on ``print`` statements which made
it difficult to control log verbosity and collect diagnostics.  This
module exposes a helper :func:`get_logger` that configures a standard
Python :class:`logging.Logger` with a consistent format.  Individual
modules can import and use it instead of ``print``.
"""

from __future__ import annotations

import logging
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-level logger with basic configuration."""

    logger = logging.getLogger(name if name else "deployable")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

