"""Deterministic archive/cache/UI/network-policy cases; no internet requests."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QObject, Signal, QByteArray, QEventLoop, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QNetworkRequest, QNetworkReply

from ecas.ingestion.nasa_archive import (
    parse_spectra, spectra_search, spectrum_url, allowed_url, store_spectrum, read_cached, cache_entries,
    MAX_BYTES, INTERFACE,
    matching_search_url,
)
from ecas.ingestion.nasa_network import PublicNasaHttp
from ecas.ui.nasa_browser import NasaArchiveBrowser

DATA = Path(__file__).resolve().parents[1] / "data/NASA/2026-10-27"
RAW = (DATA / "wasp39b-spectra-metadata.json").read_bytes()
TABLE = (DATA / "feinstein-2023.tbl").read_bytes()
RECORD = next(r for r in json.loads(RAW) if r["bibcode"] == "2023Natur.614..670F")
PAGE = b"FF_InitPage('/work/abc', '/workspace/TMP_example_123', '/exodata/FDL')"
URL = spectrum_url(PAGE, RECORD)
EVIDENCE = {"url": spectra_search("WASP-39 b"), "raw": RAW}


@pytest.fixture(scope="module", autouse=True)
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


@pytest.mark.parametrize("url", ["http://exoplanetarchive.ipac.caltech.edu/TAP/sync",
    "https://user:password@exoplanetarchive.ipac.caltech.edu/TAP/sync",
    "https://example.org/TAP/sync", "https://exoplanetarchive.ipac.caltech.edu/other",
    "https://exoplanetarchive.ipac.caltech.edu/TAP/sync#fragment"])
def test_rejects_unapproved_network_destinations(url):
    assert not allowed_url(url)


def test_fresh_workspace_used_and_changed_layout_fails():
    assert "/TMP_example_123/" in URL
    assert URL.endswith(RECORD["spec_path"])
    with pytest.raises(ValueError): spectrum_url(b"<html>changed interface</html>", RECORD)
    bad = dict(RECORD, spec_path="../../secrets.tbl")
    with pytest.raises(ValueError): spectrum_url(PAGE, bad)


@pytest.mark.parametrize("change", [{"pl_name": "Other b"}, {"num_datapoints": True},
    {"num_datapoints": 0}, {"spec_path": "../outside.tbl"}, {"spec_type": "unknown"},
    {"minwavelng": -1}, {"minwavelng": 99, "maxwavelng": 1}, {"extra": "bad"}])
def test_metadata_validation(change):
    with pytest.raises(ValueError):
        parse_spectra(json.dumps([dict(RECORD, **change)]).encode(), "WASP-39 b")


def test_cache_registration_and_offline_revalidation(tmp_path):
    source = store_spectrum(tmp_path, RECORD, TABLE, URL, EVIDENCE)
    manifest, loaded = read_cached(source.parent)
    assert source == loaded and manifest["metadata"] == RECORD
    assert source.read_bytes() == TABLE
    assert len(cache_entries(tmp_path)[0]) == 1
    source.write_bytes(TABLE + b" ")
    with pytest.raises(ValueError): read_cached(source.parent)
    assert cache_entries(tmp_path) == ([], 1)


def test_lowercase_search_preserves_original_evidence_and_reopens(tmp_path):
    evidence = dict(EVIDENCE, url=spectra_search('wasp-39 b'))
    source = store_spectrum(tmp_path, RECORD, TABLE, URL, evidence)
    manifest, _ = read_cached(source.parent)
    assert manifest['metadata_source_url'] == evidence['url']
    assert manifest['metadata']['pl_name'] == 'WASP-39 b'


def test_search_evidence_accepts_parameter_order_and_unicode_target_casing():
    url = spectra_search('wasp-39 b')
    base, query = url.split('?', 1)
    reordered = base + '?' + '&'.join(reversed(query.split('&')))
    assert matching_search_url(reordered, 'WASP-39 b')
    assert matching_search_url(spectra_search('étoile b'), 'ÉTOILE b')


@pytest.mark.parametrize('mutation', [
    lambda url: url + '&format=json',
    lambda url: url + '&format=',
    lambda url: url + '&query=',
    lambda url: url + '&extra=',
    lambda url: url + '&broken',
    lambda url: url + '#fragment',
    lambda url: url.replace('format=json', 'format=JSON'),
    lambda url: url.replace('https:', 'http:'),
    lambda url: url.replace('exoplanetarchive.ipac.caltech.edu', 'example.org'),
    lambda url: url.replace('WASP-39', 'OTHER-39'),
    lambda url: 'https://[invalid',
    lambda url: None,
])
def test_search_evidence_rejects_ambiguous_malformed_or_other_queries(mutation):
    assert not matching_search_url(mutation(spectra_search('WASP-39 b')), 'WASP-39 b')


def test_changed_metadata_and_partial_cache_are_never_accepted(tmp_path):
    source = store_spectrum(tmp_path, RECORD, TABLE, URL, EVIDENCE)
    (source.parent / "metadata.json").write_bytes(b"[]")
    with pytest.raises(ValueError): read_cached(source.parent)
    with pytest.raises(ValueError): store_spectrum(tmp_path, RECORD, b"invalid", URL, EVIDENCE)
    assert cache_entries(tmp_path) == ([], 2)


def test_malformed_manifest_is_excluded_without_hiding_valid_cache(tmp_path):
    valid = store_spectrum(tmp_path, RECORD, TABLE, URL, EVIDENCE)
    invalid = store_spectrum(tmp_path, RECORD, TABLE, URL, EVIDENCE)
    (invalid.parent / "record.json").write_text("[]")
    entries, excluded = cache_entries(tmp_path)
    assert [source for _, source in entries] == [valid]
    assert excluded == 1


def test_identity_mismatch_and_bad_evidence_do_not_register(tmp_path):
    bad = dict(RECORD, num_datapoints=1)
    evidence = dict(EVIDENCE, raw=json.dumps([bad]).encode())
    with pytest.raises(ValueError): store_spectrum(tmp_path, bad, TABLE, URL, evidence)
    with pytest.raises(ValueError): store_spectrum(tmp_path, RECORD, TABLE, URL, {"url": URL, "raw": RAW})
    assert cache_entries(tmp_path) == ([], 1)


def test_cache_rejects_changed_source_url_and_links_before_loading(tmp_path):
    source = store_spectrum(tmp_path, RECORD, TABLE, URL, EVIDENCE)
    manifest = source.parent / "record.json"
    record = json.loads(manifest.read_text())
    record["source_url"] = "https://example.org/" + RECORD["spec_path"]
    manifest.write_text(json.dumps(record))
    with pytest.raises(ValueError): read_cached(source.parent)
    with patch.object(Path, "is_symlink", return_value=True):
        with pytest.raises(ValueError): read_cached(source.parent)


class FakeHttp:
    def __init__(self): self.calls = []; self.callback = None
    def get(self, url, callback): self.calls.append(url); self.callback = callback
    def complete(self, raw, error=None):
        callback, self.callback = self.callback, None
        callback(raw, error)
    def cancel(self):
        if self.callback: self.complete(None, "cancelled")


def test_browser_search_download_cache_and_reopen_without_network(tmp_path):
    http = FakeHttp()
    widget = NasaArchiveBrowser(cache_root=tmp_path, http=http)
    loaded = []
    widget.spectrumReady.connect(loaded.append)
    widget.target.setText("WASP-39 b")
    widget.search()
    assert widget.busy and not widget.search_button.isEnabled()
    http.complete(RAW)
    idx = next(i for i, item in enumerate(widget.items) if item["metadata"]["bibcode"] == RECORD["bibcode"])
    widget.results.setCurrentRow(idx)
    widget.load_selected()
    assert http.calls[-1] == INTERFACE
    http.complete(PAGE)
    assert http.calls[-1] == URL
    http.complete(TABLE)
    assert len(loaded) == 1 and Path(loaded[0]).read_bytes() == TABLE
    call_count = len(http.calls)
    widget.show_cache()
    widget.results.setCurrentRow(0)
    widget.load_selected()
    assert len(loaded) == 2 and len(http.calls) == call_count
    widget.close()


def test_cancel_or_malformed_search_blocks_download(tmp_path):
    http = FakeHttp()
    widget = NasaArchiveBrowser(cache_root=tmp_path, http=http)
    widget.target.setText("WASP-39 b")
    widget.search()
    widget.cancel()
    assert not widget.busy and not widget.load_button.isEnabled()
    widget.search()
    http.complete(b"<html>error</html>")
    assert not widget.busy and not widget.load_button.isEnabled()
    assert not list(tmp_path.glob("entry-*"))
    widget.close()


@pytest.mark.parametrize('failure_stage', ['page', 'table'])
def test_queued_download_failure_recovers_ui_and_preserves_display(tmp_path, failure_stage):
    """Deliver failure on a later Qt event-loop turn, through the actual window."""
    from ecas.ui.main_window import ECASWindow
    window = ECASWindow()
    http = FakeHttp()
    browser = window.nasa_browser
    browser.http = http
    browser.cache_root = tmp_path
    window._import_csv_from_path(str(DATA / 'feinstein-2023.tbl'))
    original, details = window.current_spectrum, window.current_spectrum_details
    browser.target.setText('WASP-39 b')
    browser.search()
    http.complete(RAW)
    index = next(i for i, item in enumerate(browser.items)
                 if item['metadata']['bibcode'] == RECORD['bibcode'])
    browser.results.setCurrentRow(index)
    browser.load_selected()
    if failure_stage == 'table':
        http.complete(PAGE)
    assert browser.busy and not browser.search_button.isEnabled()
    loop = QEventLoop()
    delivered = []

    def receive_later():
        try:
            http.complete(b'unsupported page' if failure_stage == 'page' else b'invalid table')
            delivered.append(True)
        finally:
            loop.quit()

    guard = QTimer()
    guard.setSingleShot(True)
    guard.timeout.connect(loop.quit)
    guard.start(1000)
    QTimer.singleShot(0, receive_later)
    try:
        loop.exec()
        assert delivered == [True]
        assert not browser.busy and browser.search_button.isEnabled()
        assert browser.cache_button.isEnabled() and not browser.cancel_button.isEnabled()
        assert 'NASA operation stopped' in browser.status.text()
        assert window.current_spectrum is original
        assert window.current_spectrum_details is details
        assert window.spectrum_table.rowCount() == 331
        assert window.spectra_plot._current_spectrum is original
        assert cache_entries(tmp_path)[0] == []
    finally:
        guard.stop()
        window.close()


def test_synchronous_request_failure_recovers_browser_controls(tmp_path):
    widget = NasaArchiveBrowser(cache_root=tmp_path, http=FakeHttp())
    widget.target.setText('WASP-39 b')
    try:
        with patch.object(widget.http, 'get', side_effect=ValueError('synthetic startup failure')):
            widget.search()
        assert not widget.busy and widget.search_button.isEnabled()
        assert widget.cache_button.isEnabled() and widget.target.isEnabled()
        assert not widget.cancel_button.isEnabled()
        assert 'synthetic startup failure' in widget.status.text()
    finally:
        widget.close()


@pytest.mark.parametrize('schema_index', [0, 1])
def test_actual_window_reopens_cached_table_with_metadata_under_either_csv_schema(tmp_path, schema_index):
    from ecas.ui.main_window import ECASWindow
    source = store_spectrum(tmp_path, RECORD, TABLE, URL, EVIDENCE)
    window = ECASWindow()
    browser = window.nasa_browser
    http = FakeHttp()
    browser.http, browser.cache_root = http, tmp_path
    window.spectrum_schema_selector.setCurrentIndex(schema_index)
    try:
        browser.show_cache()
        browser.results.setCurrentRow(0)
        browser.load_selected()
        spectrum = window.current_spectrum
        assert spectrum.source_file == source.resolve()
        assert spectrum.row_count == 331
        assert spectrum.axis_unit == 'microns' and spectrum.signal_unit == '%'
        assert window.spectra_plot._current_spectrum is spectrum
        assert dict(window.current_spectrum_details.metadata)['PL_NAME'] == RECORD['pl_name']
        assert window.current_spectrum_details.source_sha256 == read_cached(source.parent)[0]['sha256']
        assert window.spectrum_table.columnCount() == 31
        assert http.calls == []
        with patch('ecas.ui.main_window.QMessageBox.warning'):
            window._import_csv_from_path(str(tmp_path / 'missing.tbl'))
        assert window.current_spectrum is None and window.current_spectrum_details is None
        assert window.spectrum_table.rowCount() == 0
        assert window.spectra_plot._current_spectrum is None
    finally:
        window.close()


class FakeReply(QObject):
    readyRead = Signal()
    finished = Signal()
    def __init__(self):
        super().__init__(); self.data = b""; self.status = 200; self.aborted = False
        self.network_error = QNetworkReply.NetworkError.NoError
    def setReadBufferSize(self, size): self.buffer_size = size
    def bytesAvailable(self): return len(self.data)
    def read(self, size):
        raw, self.data = self.data[:size], self.data[size:]
        return QByteArray(raw)
    def attribute(self, attribute): return self.status
    def error(self): return self.network_error
    def errorString(self): return "synthetic network result"
    def abort(self): self.aborted = True; self.finished.emit()


class FakeManager(QObject):
    authenticationRequired = Signal(object, object)
    proxyAuthenticationRequired = Signal(object, object)
    def __init__(self): super().__init__(); self.reply = FakeReply()
    def setProxy(self, proxy): self.proxy = proxy
    def get(self, request): self.request = request; return self.reply


@pytest.mark.parametrize("outcome", ["success", "redirect", "overflow", "timeout", "cancel", "auth", "proxy-auth", "server-error", "tls"])
def test_http_policy_deadline_limits_and_cleanup(outcome):
    manager = FakeManager()
    client = PublicNasaHttp(manager=manager)
    result = []
    client.get(EVIDENCE["url"], lambda raw, error: result.append((raw, error)))
    req = manager.request
    assert req.attribute(QNetworkRequest.Attribute.RedirectPolicyAttribute) == QNetworkRequest.RedirectPolicy.ManualRedirectPolicy
    assert req.attribute(QNetworkRequest.Attribute.CookieLoadControlAttribute) == QNetworkRequest.LoadControl.Manual
    assert req.attribute(QNetworkRequest.Attribute.CookieSaveControlAttribute) == QNetworkRequest.LoadControl.Manual
    assert req.attribute(QNetworkRequest.Attribute.AuthenticationReuseAttribute) == QNetworkRequest.LoadControl.Manual
    assert not req.rawHeader("Authorization")
    if outcome == "timeout": client.timer.timeout.emit()
    elif outcome == "cancel": client.cancel()
    elif outcome == "auth": manager.authenticationRequired.emit(manager.reply, None)
    elif outcome == "proxy-auth": manager.proxyAuthenticationRequired.emit(None, None)
    else:
        manager.reply.status = 302 if outcome == "redirect" else 500 if outcome == "server-error" else 200
        if outcome == "tls": manager.reply.network_error = QNetworkReply.NetworkError.SslHandshakeFailedError
        manager.reply.data = b"x" * (MAX_BYTES + 1) if outcome == "overflow" else b"[]"
        manager.reply.readyRead.emit()
        if not manager.reply.aborted: manager.reply.finished.emit()
    assert len(result) == 1 and client.reply is None and not client.timer.isActive()
    assert (result[0][1] is None) == (outcome == "success")
    if outcome != "success": assert result[0][0] is None


class TrackingReply(FakeReply):
    def __init__(self, deferred_abort=False):
        super().__init__()
        self.deferred_abort = deferred_abort
        self.deleted = False

    def abort(self):
        self.aborted = True
        if not self.deferred_abort:
            self.finished.emit()

    def deleteLater(self):
        self.deleted = True


class SequenceManager(FakeManager):
    def __init__(self, deferred_abort=False):
        super().__init__()
        self.replies = []
        self.deferred_abort = deferred_abort

    def get(self, request):
        reply = TrackingReply(self.deferred_abort)
        self.replies.append(reply)
        return reply


@pytest.mark.parametrize('deferred_abort', [False, True])
@pytest.mark.parametrize('trigger', ['finish-overflow', 'stream-overflow', 'cancel'])
def test_failure_callback_can_start_next_request_without_old_reply_corruption(deferred_abort, trigger):
    manager = SequenceManager(deferred_abort)
    client = PublicNasaHttp(manager=manager)
    results = []

    def failed(raw, error):
        results.append(('first', raw, error))
        client.get(EVIDENCE['url'], lambda body, failure: results.append(('second', body, failure)))

    client.get(EVIDENCE['url'], failed)
    first = manager.replies[0]
    try:
        if trigger == 'cancel':
            client.cancel()
        else:
            first.data = b'x' * (MAX_BYTES + 1)
            (first.finished if trigger == 'finish-overflow' else first.readyRead).emit()
        if deferred_abort:
            first.finished.emit()  # A delayed abort completion belongs to first.
        second = manager.replies[1]
        assert len(results) == 1 and results[0][1] is None and results[0][2]
        assert client.reply is second and client.timer.isActive()
        assert not second.deleted and not second.aborted
        second.data = b'['
        second.readyRead.emit()
        second.data = b']'
        second.readyRead.emit()
        second.finished.emit()
        assert len(results) == 2 and results[1] == ('second', b'[]', None)
        assert client.reply is None and not client.timer.isActive()
    finally:
        client.timer.stop()


def test_success_chaining_ignores_late_signals_from_previous_reply():
    manager = SequenceManager()
    client = PublicNasaHttp(manager=manager)
    results = []

    def completed(raw, error):
        results.append((raw, error))
        client.get(EVIDENCE['url'], lambda body, failure: results.append((body, failure)))

    client.get(EVIDENCE['url'], completed)
    first = manager.replies[0]
    first.data = b'first'
    first.finished.emit()
    second = manager.replies[1]
    try:
        # Queued/late signals must never drain or complete the new request.
        first.data = b'stale'
        first.readyRead.emit()
        first.finished.emit()
        assert client.reply is second and client.timer.isActive()
        assert results == [(b'first', None)] and not second.deleted
        second.data = b'new'
        second.finished.emit()
        assert results == [(b'first', None), (b'new', None)]
        assert client.reply is None and not client.timer.isActive()
    finally:
        client.timer.stop()


def test_reentry_url_guard_and_unrelated_authentication_preserve_active_request():
    manager = SequenceManager()
    client = PublicNasaHttp(manager=manager)
    results = []
    with pytest.raises(ValueError):
        client.get('https://example.org/TAP/sync', lambda *_: None)
    assert manager.replies == []
    client.get(EVIDENCE['url'], lambda raw, error: results.append((raw, error)))
    active = manager.replies[0]
    try:
        with pytest.raises(ValueError):
            client.get(EVIDENCE['url'], lambda *_: None)
        unrelated = TrackingReply()
        manager.authenticationRequired.emit(unrelated, None)
        assert client.reply is active and not active.aborted
        assert client.timer.isActive() and results == []
        active.data = b'ok'
        active.finished.emit()
        assert results == [(b'ok', None)] and client.reply is None
    finally:
        client.timer.stop()


@pytest.mark.parametrize('overflow', [False, True])
def test_response_cap_across_multiple_ready_read_events(overflow):
    manager = SequenceManager()
    client = PublicNasaHttp(manager=manager)
    results = []
    client.get(EVIDENCE['url'], lambda raw, error: results.append((raw, error)))
    reply = manager.replies[0]
    try:
        for size in (MAX_BYTES // 2, MAX_BYTES // 2):
            reply.data = b'x' * size
            reply.readyRead.emit()
        assert results == []
        if overflow:
            reply.data = b'x'
            reply.readyRead.emit()
            assert len(results) == 1 and results[0][0] is None and results[0][1]
            assert reply.aborted
        else:
            reply.finished.emit()
            assert results == [(b'x' * MAX_BYTES, None)]
        assert client.reply is None and not client.timer.isActive()
    finally:
        client.timer.stop()
