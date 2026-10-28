"""Bounded ExoMol annotated master-index parsing and offline identity search.

Catalogue membership is not spectral-product availability or scientific suitability.
"""
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import re
from urllib.parse import quote

MAX_BYTES = 1024*1024


class CatalogueError(ValueError):
    pass


@dataclass(frozen=True)
class CatalogueEntry:
    formula: str
    names: tuple[str, ...]
    inchi_key: str
    isotopologue: str
    isotope_formula: str
    dataset: str
    version: str

    @property
    def definition_url(self):
        parts = (self.formula, self.isotopologue, self.dataset,
                 f'{self.isotopologue}__{self.dataset}.def')
        return 'https://www.exomol.com/db/' + '/'.join(quote(p, safe='') for p in parts)


@dataclass(frozen=True)
class ExomolCatalogue:
    version: str
    entries: tuple[CatalogueEntry, ...]
    source_sha256: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class CatalogueSearch:
    entries: tuple[CatalogueEntry, ...]
    total_matches: int
    truncated: bool
    formulas: tuple[str, ...]


def parse_catalogue(raw):
    if not isinstance(raw, bytes) or not raw or len(raw)>MAX_BYTES:
        raise CatalogueError('Require nonempty catalogue bytes within 1 MiB')
    try:
        lines = [line for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
    except UnicodeError as error:
        raise CatalogueError('Catalogue must be UTF-8 text') from error
    if len(lines)>20000:
        raise CatalogueError('Catalogue exceeds line limit')
    position = 0
    warnings = []

    def take(label):
        nonlocal position
        if position >= len(lines):
            raise CatalogueError(f'Truncated catalogue; expected {label}')
        value, separator, actual = lines[position].partition('#')
        position += 1
        value = value.strip()
        if not separator or actual.strip() != label or not value or len(value)>512 or any(ord(c)<32 or ord(c)==127 for c in value):
            raise CatalogueError(f'Unsupported catalogue field at line {position}: expected {label}')
        return value

    def count(label, maximum=10000):
        value = take(label)
        if not re.fullmatch(r'[0-9]+', value) or int(value)>maximum:
            raise CatalogueError(f'Invalid catalogue count: {label}')
        return int(value)

    def version():
        value = take('Version number with format YYYYMMDD')
        if not re.fullmatch(r'[0-9]{8}', value):
            raise CatalogueError('Unsupported version label')
        try:
            datetime.strptime(value, '%Y%m%d')
        except ValueError:
            warnings.append(f'Provider version label {value} is not a valid calendar date; retained unchanged')
        return value

    def identifier(label):
        value = take(label)
        if '/' in value or '\\' in value or '..' in value or any(c.isspace() for c in value):
            raise CatalogueError(f'Unsafe identifier: {label}')
        return value

    if take('ID') != 'EXOMOL.master':
        raise CatalogueError('Not an ExoMol master catalogue')
    revision = version()
    molecules = count('Number of molecules in the database', 1000)
    isotope_count = count('Number of isotopologues in the database')
    datasets = count('Number of datasets in the database')
    entries, formulas, identities = [], set(), set()
    for _ in range(molecules):
        names = tuple(take('Name of the molecule') for _ in range(count('Number of molecule names listed', 100)))
        formula = identifier('Molecule chemical formula')
        if formula in formulas:
            raise CatalogueError('Repeated molecule block')
        formulas.add(formula)
        declared_isotopes = count('Number of isotopologues considered')
        block_isotopes = set()
        # A molecule may contain several datasets for one isotope. The block's
        # count is unique isotopologues, not the number of five-field dataset rows.
        while position < len(lines) and lines[position].partition('#')[2].strip() == 'Inchi key of isotopologue':
            key = identifier('Inchi key of isotopologue')
            slug = identifier('Iso-slug')
            isotope_formula = identifier('IsoFormula')
            dataset = identifier('Isotopologue dataset name')
            entry = CatalogueEntry(formula, names, key, slug, isotope_formula, dataset, version())
            identity = (formula, slug, dataset)
            if identity in identities:
                raise CatalogueError('Repeated molecule/isotopologue/dataset record')
            identities.add(identity)
            block_isotopes.add(slug)
            entries.append(entry)
            if len(entries)>10000:
                raise CatalogueError('Catalogue exceeds dataset limit')
        if len(block_isotopes) != declared_isotopes:
            raise CatalogueError('Declared molecule isotope count does not match its datasets')
    if position != len(lines):
        raise CatalogueError('Unexpected trailing catalogue fields')
    if len(entries) != datasets or len({(e.formula, e.isotopologue) for e in entries}) != isotope_count:
        raise CatalogueError('Declared catalogue totals do not match parsed identities')
    return ExomolCatalogue(revision, tuple(entries), sha256(raw).hexdigest(), tuple(dict.fromkeys(warnings)))


def search_catalogue(catalogue, query, *, limit=50):
    if not isinstance(query, str) or not query.strip() or len(query)>256 or any(ord(c)<32 or ord(c)==127 for c in query):
        raise CatalogueError('Require a nonempty molecule name, formula or provider identifier')
    if type(limit) is not int or not 1<=limit<=200:
        raise CatalogueError('Search limit must be between 1 and 200')
    query = ' '.join(query.split())
    folded = query.casefold()
    # Formula/isotope spelling is case-sensitive. Provider names and dataset names
    # use case-insensitive exact matching; do not silently resolve ambiguous aliases.
    hits = tuple(e for e in catalogue.entries if query in (e.formula, e.isotopologue, e.isotope_formula)
                 or folded == e.inchi_key.casefold() or folded == e.dataset.casefold()
                 or folded in (' '.join(name.split()).casefold() for name in e.names))
    return CatalogueSearch(hits[:limit], len(hits), len(hits)>limit,
                           tuple(sorted({e.formula for e in hits})))
