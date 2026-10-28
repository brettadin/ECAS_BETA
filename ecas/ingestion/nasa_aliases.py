"""Resolve a user name only when NASA explicitly identifies one requested planet."""
import json
from urllib.parse import urlencode

from .nasa_discovery import planet_search, _unique_object, _invalid_constant

ENDPOINT = 'https://exoplanetarchive.ipac.caltech.edu/cgi-bin/Lookup/nph-aliaslookup.py'


def alias_search(name):
    return ENDPOINT + '?' + urlencode({'objname': planet_search(name).name})


def parse_aliases(raw, requested_name):
    requested_name = planet_search(requested_name).name
    if type(raw) is not bytes or not raw or len(raw) > 1048576:
        raise ValueError('Empty or oversized NASA name response')
    try:
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                          parse_constant=_invalid_constant)
        manifest = data['manifest']
        if (manifest['lookup_status'] != 'OK'
                or manifest['requested_name'].casefold() != requested_name.casefold()):
            raise ValueError('NASA could not resolve that requested name')
        planets = data['system']['objects']['planet_set']['planets']
        if not isinstance(planets, dict) or len(planets) > 1000:
            raise ValueError('Unsupported NASA planet list')
        selected = [(key, value) for key, value in planets.items()
                    if isinstance(value, dict) and value.get('requested_object') == 'True']
        if len(selected) != 1:
            raise ValueError('Enter a specific planet name; NASA did not uniquely identify one planet')
        key, item = selected[0]
        canonical = planet_search(item['alias_set']['default_name']).name
        if canonical != key or canonical != manifest['resolved_name']:
            raise ValueError('NASA name resolution returned inconsistent planet identities')
        return canonical
    except (KeyError, TypeError, AttributeError, UnicodeError, RecursionError) as error:
        raise ValueError('Unsupported NASA name response') from error
