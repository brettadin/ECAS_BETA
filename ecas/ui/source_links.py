"""Presentation-only source links; the imported source values are never edited."""
from urllib.parse import urlsplit

NASA = 'https://exoplanetarchive.ipac.caltech.edu'


def source_link(value, *, nasa_source=False):
    if not isinstance(value, str) or any(ord(c) < 32 or ord(c) == 127 for c in value):
        return None
    if nasa_source and value.startswith('/docs/atmospheres/') and '\\' not in value:
        value = NASA + value
    try:
        parts = urlsplit(value)
        if parts.scheme not in ('https', 'http') or not parts.hostname or parts.username is not None or parts.password is not None:
            return None
        return value
    except ValueError:
        return None
