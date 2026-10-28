import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QObject, Signal, QByteArray, QEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QNetworkRequest, QNetworkReply

from ecas.ingestion.exomol_catalogue_cache import CATALOGUE_URL, load_catalogue, store_catalogue
from ecas.ingestion.exomol_network import PublicExomolCatalogueHttp
from ecas.ui.molecular_browser import MolecularReferenceBrowser
from ecas.ui.main_window import ECASWindow

DATA = Path(__file__).resolve().parents[1]/'data/ExoMol/2026-10-28/exomol.all'
RAW = DATA.read_bytes()


@pytest.fixture(scope='session', autouse=True)
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance
    # Keep one QApplication alive across modules. Each test closes its own widgets;
    # do not flush/delete unrelated modules' deferred Qt objects during teardown.


class FakeHttp:
    def __init__(self): self.callback = None
    def get(self, callback): self.callback = callback
    def finish(self, raw=RAW, error=None):
        callback, self.callback = self.callback, None
        callback(raw, error)
    def cancel(self):
        if self.callback: self.finish(None, 'cancelled')


def test_browser_offline_search_ambiguity_and_selection(tmp_path):
    browser = MolecularReferenceBrowser(cache_root=tmp_path/'cache', http=FakeHttp())
    try:
        assert 'Bundled' in browser.source.text() and not browser.cache_root.exists()
        browser.query.setText('Water')
        browser.search_button.click()
        assert browser.results.count() == 5
        browser.results.setCurrentRow(0)
        assert 'not established' in browser.details.text()
        browser.query.setText('Phosphine')
        browser.query.returnPressed.emit()
        assert browser.results.count() == 2 and 'Ambiguous' in browser.status.text()
        browser.query.setText('synthetic-nonexistent-molecule')
        browser.search_button.click()
        assert browser.results.count() == 0 and 'No matches' in browser.status.text()
        assert 'Select an entry' in browser.details.text()
    finally: browser.shutdown(); browser.close()


def test_refresh_cache_reopen_without_source_or_network(tmp_path):
    http = FakeHttp()
    browser = MolecularReferenceBrowser(cache_root=tmp_path/'cache', http=http)
    try:
        browser.query.setText('CO2')
        browser.refresh_button.click()
        assert browser.busy and not browser.search_button.isEnabled()
        http.finish()
        assert not browser.busy and browser.results.count() == 13
        assert 'Cached' in browser.source.text()
    finally: browser.shutdown(); browser.close()
    reopened = MolecularReferenceBrowser(cache_root=tmp_path/'cache', bundled_path=tmp_path/'missing', http=FakeHttp())
    try:
        reopened.query.setText('Water')
        reopened.search_button.click()
        assert reopened.results.count() == 5 and 'Cached' in reopened.source.text()
        assert reopened.http.callback is None
    finally: reopened.shutdown(); reopened.close()


@pytest.mark.parametrize('failure', ['cancel', 'invalid_response', 'start_error', 'disk_error'])
def test_failed_refresh_preserves_search_and_cache(tmp_path, failure):
    store_catalogue(tmp_path/'cache', RAW)
    original_bytes = (tmp_path/'cache/catalogue.json').read_bytes()
    http = FakeHttp()
    browser = MolecularReferenceBrowser(cache_root=tmp_path/'cache', http=http)
    try:
        browser.query.setText('Water'); browser.search()
        original = browser.catalogue
        if failure == 'start_error':
            with patch.object(http, 'get', side_effect=OSError('synthetic start error')): browser.refresh_button.click()
        else:
            browser.refresh_button.click()
            if failure == 'cancel': browser.cancel_button.click()
            elif failure == 'invalid_response': http.finish(b'<html>unavailable</html>')
            else:
                with patch('ecas.ingestion.exomol_catalogue_cache.os.replace', side_effect=OSError('synthetic disk failure')):
                    http.finish()
        assert browser.catalogue is original and browser.results.count() == 5
        assert not browser.busy and browser.search_button.isEnabled()
        assert 'Previous catalogue unchanged' in browser.status.text()
        assert (tmp_path/'cache/catalogue.json').read_bytes() == original_bytes
        assert not list((tmp_path/'cache').glob('*.tmp'))
    finally: browser.shutdown(); browser.close()


def test_corrupt_cache_is_reported_and_bundled_snapshot_fallback_used(tmp_path):
    store_catalogue(tmp_path, RAW)
    envelope = json.loads((tmp_path/'catalogue.json').read_text())
    envelope['sha256'] = '0'*64
    (tmp_path/'catalogue.json').write_text(json.dumps(envelope))
    with pytest.raises(ValueError): load_catalogue(tmp_path)
    browser = MolecularReferenceBrowser(cache_root=tmp_path, http=FakeHttp())
    try:
        assert 'Cached catalogue could not be loaded' in browser.status.text()
        assert 'Bundled' in browser.source.text()
    finally: browser.shutdown(); browser.close()


@pytest.mark.parametrize('field,value', [('source_url', 'https://example.org/index'),
    ('schema', 'unknown'), ('retrieved_utc', '2026-10-28T12:00:00'), ('raw_base64', '!!invalid!!')])
def test_cache_rejects_invalid_source_format_and_provenance(tmp_path, field, value):
    store_catalogue(tmp_path, RAW)
    path = tmp_path/'catalogue.json'
    envelope = json.loads(path.read_text())
    envelope[field] = value
    path.write_text(json.dumps(envelope))
    with pytest.raises(ValueError): load_catalogue(tmp_path)


def test_missing_cache_read_and_invalid_store_have_no_directory_side_effect(tmp_path):
    root = tmp_path/'cache'
    assert load_catalogue(root) is None and not root.exists()
    with pytest.raises(ValueError): store_catalogue(root, b'invalid source')
    assert not root.exists()


def test_no_local_catalogue_can_recover_via_refresh_and_close_ignores_callback(tmp_path):
    http = FakeHttp()
    browser = MolecularReferenceBrowser(cache_root=tmp_path/'cache', bundled_path=tmp_path/'missing', http=http)
    try:
        assert not browser.search_button.isEnabled() and browser.refresh_button.isEnabled()
        browser.refresh(); http.finish()
        assert browser.search_button.isEnabled()
        browser.refresh()
        callback = http.callback
        browser.shutdown()
        previous = browser.catalogue
        callback(b'invalid', None)
        assert browser.catalogue is previous
    finally: browser.close()


def test_actual_window_comparisons_tab_contains_search_and_preserves_display(tmp_path):
    window = ECASWindow(projects_dir=tmp_path/'projects', reference_cache_dir=tmp_path/'cache')
    try:
        window.navigation.setCurrentRow(3)
        browser = window.reference_browser
        browser.query.setText('Water'); browser.search_button.click()
        assert browser.results.count() == 5
        assert window.current_spectrum is None and not (tmp_path/'cache').exists()
        assert window.pages.currentIndex() == 3
        assert browser.http is None  # offline use creates no network manager
    finally: window.close()


def test_real_qt_manager_creation_on_refresh_and_window_shutdown(tmp_path):
    # Exercise real manager ownership/destruction without making an HTTP request.
    with patch.object(PublicExomolCatalogueHttp, 'get', lambda self, callback: callback(RAW, None)):
        for index in range(5):
            window = ECASWindow(projects_dir=tmp_path/'projects', reference_cache_dir=tmp_path/f'cache{index}')
            browser = window.reference_browser
            browser.refresh_button.click()
            assert isinstance(browser.http, PublicExomolCatalogueHttp)
            assert 'Cached' in browser.source.text()
            window.close()
            assert browser.http.closed
            QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


class Reply(QObject):
    readyRead = Signal()
    finished = Signal()
    def __init__(self, raw=b'', status=200, queued=False):
        super().__init__(); self.raw=raw; self.status=status; self.queued=queued; self.deleted=False
    def setReadBufferSize(self, size): pass
    def bytesAvailable(self): return len(self.raw)
    def read(self, size):
        block, self.raw = self.raw[:size], self.raw[size:]
        return QByteArray(block)
    def abort(self):
        if not self.queued: self.finished.emit()
    def attribute(self, attr): return self.status
    def error(self): return QNetworkReply.NetworkError.NoError
    def errorString(self): return 'synthetic'
    def deleteLater(self): self.deleted=True


class Manager(QObject):
    authenticationRequired = Signal(object, object)
    proxyAuthenticationRequired = Signal(object, object)
    def __init__(self, replies): super().__init__(); self.replies=list(replies); self.requests=[]
    def setProxy(self, proxy): pass
    def get(self, request): self.requests.append(request); return self.replies.pop(0)


def test_http_fixed_origin_and_anonymous_policy():
    reply = Reply(RAW)
    manager = Manager([reply]); client = PublicExomolCatalogueHttp(manager=manager)
    result=[]; client.get(lambda raw, error: result.append((raw,error)))
    request=manager.requests[0]
    assert request.url().toString() == CATALOGUE_URL
    assert not request.rawHeader('Authorization') and not request.rawHeader('Cookie')
    assert client.timer.interval() == 15000
    for attr in (QNetworkRequest.Attribute.CookieLoadControlAttribute, QNetworkRequest.Attribute.CookieSaveControlAttribute,
                 QNetworkRequest.Attribute.AuthenticationReuseAttribute):
        assert request.attribute(attr) == QNetworkRequest.LoadControl.Manual
    assert request.attribute(QNetworkRequest.Attribute.RedirectPolicyAttribute) == QNetworkRequest.RedirectPolicy.ManualRedirectPolicy
    with pytest.raises(ValueError): client.get(lambda *_: None)
    reply.finished.emit()
    assert result == [(RAW, None)] and reply.deleted and client.reply is None


@pytest.mark.parametrize('queued', [False, True])
def test_overflow_and_chained_request_do_not_corrupt_new_reply(queued):
    old, new = Reply(b'x'*1048577, queued=queued), Reply(RAW)
    client = PublicExomolCatalogueHttp(manager=Manager([old,new]))
    results=[]
    def failed(raw,error):
        results.append((raw,error))
        client.get(lambda body, problem: results.append((body,problem)))
    client.get(failed)
    old.finished.emit()
    assert client.reply is new and not new.deleted and len(results)==1
    old.finished.emit()
    assert client.reply is new and len(results)==1
    new.finished.emit()
    assert results[0][0] is None and 'exceeds' in results[0][1]
    assert results[1] == (RAW,None)


@pytest.mark.parametrize('kind', ['timeout', 'auth', 'proxy', 'redirect', 'http_error'])
def test_network_failures_complete_once_and_release_client(kind):
    reply=Reply(status=302 if kind=='redirect' else 503 if kind=='http_error' else 200)
    manager=Manager([reply]); client=PublicExomolCatalogueHttp(manager=manager)
    results=[]; client.get(lambda *args: results.append(args))
    if kind=='timeout': client.timer.timeout.emit()
    elif kind=='auth': manager.authenticationRequired.emit(reply,None)
    elif kind=='proxy': manager.proxyAuthenticationRequired.emit(None,None)
    else: reply.finished.emit()
    reply.finished.emit()
    assert len(results)==1 and results[0][0] is None and results[0][1]
    assert client.reply is None and not client.timer.isActive()


def test_shutdown_discards_late_signals_and_forbids_new_request():
    reply=Reply(queued=True)
    manager=Manager([reply]); client=PublicExomolCatalogueHttp(manager=manager)
    results=[]; client.get(lambda *args: results.append(args))
    client.shutdown()
    reply.finished.emit()
    assert not results and client.closed and not client.timer.isActive()
    with pytest.raises(ValueError, match='closed'): client.get(lambda *_: None)
