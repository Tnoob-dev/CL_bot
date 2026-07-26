"""CinemaLibraryBot application package.

Importing the package loads configuration (and the runtime ``.env``) up front,
so every submodule sees a consistent environment regardless of import order or
the process working directory.
"""

from cinemalibrarybot.config import settings

__all__ = ["settings"]
