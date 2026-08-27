"""Compatibility wrapper for Phemacast Pulse directory normalization.

Phemacast owns the Pulse-oriented terminology while reusing the generic
directory-normalization helpers provided by Prompits Lite, matching the
original FinMAS module boundary.
"""

from prompits_lite.directory_runtime import (
    DIRECTORY_RUNTIME_VERSION,
    JsonObject,
    build_pulse_definition,
    derive_pulse_id,
    normalize_pulse_pair_entry,
    normalize_runtime_pulse_entry,
)


PULSE_RUNTIME_VERSION = DIRECTORY_RUNTIME_VERSION


__all__ = [
    "DIRECTORY_RUNTIME_VERSION",
    "PULSE_RUNTIME_VERSION",
    "JsonObject",
    "build_pulse_definition",
    "derive_pulse_id",
    "normalize_pulse_pair_entry",
    "normalize_runtime_pulse_entry",
]
