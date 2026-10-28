"""Presentation of saved project facts; never reads or rewrites source files."""
from html import escape
import math


def _text(value):
    return ' '.join(value.split()) if isinstance(value, str) else ''


def project_label(record):
    """Return plain list text and an escaped tooltip from a loaded record.

    Prefer the saved archive listing for the heading. Keep table descriptions
    separately attributed, including conflicting years or instrument names.
    Missing descriptive metadata is not an integrity failure or a scientific fact.
    """
    spectrum = record.spectrum
    attachment = record.attachment or {}
    provenance = attachment.get('provenance', {})
    if not isinstance(provenance, dict):
        provenance = {}
    cache = provenance.get('cache_record', {})
    archive = cache.get('metadata', {}) if isinstance(cache, dict) else {}
    if not isinstance(archive, dict):
        archive = {}
    try:
        table = dict(provenance.get('table_metadata', ()))
    except (TypeError, ValueError):
        table = {}
    filename = str(spectrum.source_file).replace('\\', '/').rsplit('/', 1)[-1]
    publication = _text(archive.get('authors')) or _text(table.get('REFERENCE'))
    planet = _text(archive.get('pl_name')) or _text(table.get('PL_NAME'))
    instrument = _text(archive.get('instrument')) or _text(table.get('INSTRUMENT'))
    kind = _text(archive.get('spec_type')) or _text(table.get('SPEC_TYPE')) or _text(spectrum.signal_type)
    heading = ' — '.join(part for part in (planet, publication or filename) if part)
    integrity = 'source preserved' if record.attachment is not None else 'legacy: no source attachment'
    summary = ' | '.join(part for part in (instrument, kind, f'{spectrum.row_count} rows', integrity) if part)
    label = f'{record.record_id}: {heading}\n{summary}'
    details = [f'Record: {record.record_id}', f'Source filename: {filename}',
               f'Original path: {spectrum.source_file}']
    fields = (('Planet', 'pl_name', 'PL_NAME'), ('Publication', 'authors', 'REFERENCE'),
              ('Instrument', 'instrument', 'INSTRUMENT'), ('Facility', 'facility', 'FACILITY'),
              ('Spectrum type', 'spec_type', 'SPEC_TYPE'))
    for title, archive_key, table_key in fields:
        archive_value, table_value = _text(archive.get(archive_key)), _text(table.get(table_key))
        if archive_value:
            details.append(f'Archive {title.lower()}: {archive_value}')
        if table_value:
            details.append(f'Table {title.lower()}: {table_value}')
        if archive_value and table_value and archive_value != table_value:
            details.append(f'{title}: saved source descriptions differ; neither was corrected.')
    if _text(archive.get('bibcode')):
        details.append(f'Archive publication identifier: {archive["bibcode"]}')
    # Use imported coordinates and their established unit, not assumed units for
    # the archive listing's independent min/max fields.
    coordinates = [row.get('wavelength') for row in spectrum.rows]
    coordinates = [value for value in coordinates if type(value) in (int, float) and math.isfinite(value)]
    if coordinates:
        details.append(f'Imported wavelength range: {min(coordinates):g}–{max(coordinates):g} '
                       f'({_text(spectrum.axis_unit) or "unit not established"})')
    if attachment.get('source_sha256'):
        details.append(f'Source SHA-256: {attachment["source_sha256"]}')
    details.append(integrity)
    # Qt tooltips detect rich text. Escape provider/local text before formatting.
    return label, '<qt>' + '<br>'.join(escape(line) for line in details) + '</qt>'
