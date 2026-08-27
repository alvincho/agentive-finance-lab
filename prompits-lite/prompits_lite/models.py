"""Compatibility exports for canonical Prompits value objects.

The original project defines these objects in ``prompits.core`` modules.  This
flat Lite package re-exports them here without introducing a second contract.
"""

from typing import Any, Dict

from .message import Message
from .pit import PitAddress


JsonObject = Dict[str, Any]


__all__ = ["JsonObject", "Message", "PitAddress"]
