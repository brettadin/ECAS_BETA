"""Real-library laboratory identification; planetary transit models remain separate."""

from .library import LibraryCatalog, ReferenceDataset, discover_library, load_library_spectrum, load_reference
from .engine import ComponentResult, IdentificationResult, identify

__all__ = ["LibraryCatalog", "ReferenceDataset", "discover_library", "load_library_spectrum",
           "load_reference", "ComponentResult", "IdentificationResult", "identify"]
