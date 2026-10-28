from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QObject, Signal, QByteArray
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest

from ecas.ingestion.exomol_catalogue import parse_catalogue, search_catalogue
from ecas.ingestion.exomol_product import ProductRequest, parse_form, product_url, validate_product, supported_entry, SERVICE_URL
from ecas.ingestion.exomol_product_network import PublicExomolProductHttp, RetrievedCrossSection
from ecas.ingestion.exomol_reference_cache import store_reference, load_reference, cached_references
from ecas.ui.molecular_browser import MolecularReferenceBrowser
from ecas.ui.main_window import ECASWindow

DATA=Path(__file__).resolve().parents[1]/'data/ExoMol/2026-10-28'
FORM=(DATA/'CO2-product-form-sanitized.html').read_bytes()
LINKS=(DATA/'CO2-sample-product-links.html').read_bytes()
RAW=(DATA/'CO2-12C-16O2-500K-4000-4010-dnu1.sigma').read_bytes()
REQUEST=ProductRequest(4000,4010,500,'1')
ENTRY=next(e for e in search_catalogue(parse_catalogue((DATA/'exomol.all').read_bytes()),'CO2').entries if supported_entry(e))


@pytest.fixture(scope='session',autouse=True)
def app():
    instance=QApplication.instance() or QApplication([])
    yield instance


def result(): return RetrievedCrossSection(REQUEST,RAW,validate_product(RAW,REQUEST))


def test_live_capture_protocol_grid_and_identity():
    form=parse_form(FORM)
    assert 'SSSS' not in repr(form)
    assert b'spoon_feed=on' in form.body(REQUEST)
    assert product_url(LINKS,REQUEST)=='https://www.exomol.com'+REQUEST.product_path
    product=validate_product(RAW,REQUEST)
    assert len(product.points)==11 and product.points[0][0]==4000 and product.points[-1][0]==4010
    assert product.source_sha256=='d323b5dd2f11c87a3cd6c0dc041fd625f00d56ec05cc2f2f2fb756cb01ea9fab'
    assert product.provenance.pressure_bar==0 and product.provenance.temperature_kelvin==500


@pytest.mark.parametrize('parameters', [(0,20001,500,'1'),(4010,4000,500,'1'),(0,1,99,'1'),
    (0,1,500,'0'),(0,1,500,'0.3'),(0,1,500,'0.0000001'),(0,20000,500,'1'),
    (True,10,500,'1'),(0,10,500,'NaN')])
def test_request_bounds_and_exact_grid(parameters):
    with pytest.raises(ValueError): ProductRequest(*parameters)


@pytest.mark.parametrize('change', ['fields','action','token','error_page','dataset','pressure','units'])
def test_changed_form_fails_before_post(change):
    raw=FORM
    if change=='fields': raw=raw.replace(b'name="spoon_feed"',b'name="other"')
    elif change=='action': raw=raw.replace(b'action="/xsec/12C-16O2/"',b'action="https://example.org/"')
    elif change=='token': raw=raw.replace(b'S'*64,b'')
    elif change=='dataset': raw=raw.replace(b'line list UCL-4000',b'line list Dozen')
    elif change=='pressure': raw=raw.replace(b'zero-pressure',b'finite-pressure')
    elif change=='units': raw=raw.replace(b'/molec',b'/kilogram')
    else: raw=b'<html>Unavailable</html>'
    with pytest.raises(ValueError): parse_form(raw)


@pytest.mark.parametrize('link', ['/results/other.sigma','https://example.org/reference.sigma',
    '//www.exomol.com'+REQUEST.product_path, REQUEST.product_path+'?extra=1',
    REQUEST.product_path.replace('500K','501K')])
def test_result_link_must_match_request_exactly(link):
    with pytest.raises(ValueError): product_url(f'<a href="{link}">file</a>'.encode(),REQUEST)


def test_valid_numerical_product_with_wrong_grid_is_not_accepted():
    with pytest.raises(ValueError): validate_product(RAW,ProductRequest(4000,4009,500,'1'))
    with pytest.raises(ValueError): validate_product(RAW.replace(b'4005.000000',b'4005.100000'),REQUEST)


def test_reference_cache_offline_registration_revalidation_and_atomic_failure(tmp_path):
    stored=result()
    assert cached_references(tmp_path/'cache')==([],0) and not (tmp_path/'cache').exists()
    path=store_reference(tmp_path/'cache',stored)
    assert load_reference(path)==stored
    assert cached_references(path.parent)[0][0][0]==path
    original=path.read_bytes()
    with patch('ecas.ingestion.exomol_reference_cache.os.replace',side_effect=OSError('synthetic disk error')):
        with pytest.raises(OSError): store_reference(path.parent,stored)
    assert path.read_bytes()==original and not list(path.parent.glob('*.tmp'))
    bad=json.loads(original); bad['request']['temperature']=600
    path.write_text(json.dumps(bad))
    with pytest.raises(ValueError): load_reference(path)
    assert cached_references(path.parent)==([],1)


def test_cached_product_cannot_substitute_different_provenance(tmp_path):
    product=replace(result().product,provenance=replace(result().product.provenance,pressure_bar=1))
    with pytest.raises(ValueError): store_reference(tmp_path,RetrievedCrossSection(REQUEST,RAW,product))


def test_earlier_reference_envelope_without_catalogue_context_still_reopens(tmp_path):
    path=store_reference(tmp_path,result())
    envelope=json.loads(path.read_text())
    envelope.pop('catalogue_context'); envelope.pop('integrity_sha256')
    envelope['integrity_sha256']=sha256(json.dumps(envelope,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    path.write_text(json.dumps(envelope))
    assert load_reference(path)==result()


def test_conflicting_catalogue_identity_is_not_registered(tmp_path):
    with pytest.raises(ValueError):
        store_reference(tmp_path/'cache',result(),catalogue_context=dict(formula='H2O',isotopologue='1H2-16O',
            dataset='POKAZATEL',version='20230621',catalogue_sha256='a'*64))
    assert not (tmp_path/'cache').exists()


def test_early_v1_citation_metadata_remain_readable_without_rewrite(tmp_path):
    path=store_reference(tmp_path,result())
    envelope=json.loads(path.read_text())
    envelope['provenance']['citations']=envelope['provenance']['citations'][:2]
    envelope.pop('integrity_sha256')
    envelope['integrity_sha256']=sha256(json.dumps(envelope,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    path.write_text(json.dumps(envelope))
    original=path.read_bytes()
    reopened=load_reference(path)
    assert reopened.raw==RAW and reopened.product.provenance.citations==result().product.provenance.citations[:2]
    assert path.read_bytes()==original


class Reply(QObject):
    readyRead=Signal(); finished=Signal()
    def __init__(self,raw,status=200,headers=(),queued=False):
        super().__init__(); self.raw=raw; self.status=status; self.headers=headers; self.queued=queued; self.deleted=False
    def setReadBufferSize(self,size): pass
    def bytesAvailable(self): return len(self.raw)
    def read(self,size):
        raw,self.raw=self.raw[:size],self.raw[size:]
        return QByteArray(raw)
    def rawHeaderPairs(self): return [(QByteArray(k),QByteArray(v)) for k,v in self.headers]
    def abort(self):
        if not self.queued: self.finished.emit()
    def deleteLater(self): self.deleted=True
    def attribute(self,attr): return self.status
    def error(self): return QNetworkReply.NetworkError.NoError
    def errorString(self): return 'synthetic'


class Manager(QObject):
    authenticationRequired=Signal(object,object); proxyAuthenticationRequired=Signal(object,object)
    def __init__(self,replies): super().__init__(); self.replies=list(replies); self.requests=[]
    def setProxy(self,proxy): pass
    def get(self,request): self.requests.append(('GET',request,None)); return self.replies.pop(0)
    def post(self,request,body): self.requests.append(('POST',request,bytes(body))); return self.replies.pop(0)


def sequence():
    return [Reply(FORM,headers=[(b'Set-Cookie',b'csrftoken='+b'C'*32+b'; Path=/; Secure')]),Reply(LINKS),Reply(RAW)]


def test_three_phase_requests_only_forward_fresh_csrf_to_form_post():
    replies=sequence(); manager=Manager(replies); client=PublicExomolProductHttp(manager=manager)
    results=[]; client.download(ENTRY,REQUEST,lambda *args: results.append(args))
    for reply in replies: reply.finished.emit()
    assert len(results)==1 and results[0][0]==result() and results[0][1] is None
    assert [method for method,_,_ in manager.requests]==['GET','POST','GET']
    for index,(_,request,body) in enumerate(manager.requests):
        assert not request.rawHeader('Authorization')
        assert bool(request.rawHeader('Cookie')) == (index==1)
        assert request.attribute(QNetworkRequest.Attribute.CookieLoadControlAttribute)==QNetworkRequest.LoadControl.Manual
        assert request.attribute(QNetworkRequest.Attribute.RedirectPolicyAttribute)==QNetworkRequest.RedirectPolicy.ManualRedirectPolicy
    assert manager.requests[1][1].url().toString()==SERVICE_URL
    assert b'email' not in manager.requests[1][2]
    assert client.request is None and client.callback is None and not client.timer.isActive()


@pytest.mark.parametrize('failure', ['cookie','redirect','invalid_form','invalid_link','oversize','auth','timeout','cancel'])
def test_protocol_failure_cleans_up_once(failure):
    replies=sequence()
    if failure=='cookie': replies[0].headers=[]
    elif failure=='redirect': replies[0].status=302
    elif failure=='invalid_form': replies[0].raw=b'bad'
    elif failure=='invalid_link': replies[1].raw=b'bad'
    elif failure=='oversize': replies[0].raw=b'x'*262145
    manager=Manager(replies); client=PublicExomolProductHttp(manager=manager)
    results=[]; client.download(ENTRY,REQUEST,lambda *args: results.append(args))
    if failure=='auth': manager.authenticationRequired.emit(replies[0],None)
    elif failure=='timeout': client.timer.timeout.emit()
    elif failure=='cancel': client.cancel()
    else:
        replies[0].finished.emit()
        if failure=='invalid_link': replies[1].finished.emit()
    replies[0].finished.emit()
    assert len(results)==1 and results[0][0] is None and results[0][1]
    assert client.reply is None and client.callback is None and not client.timer.isActive()


@pytest.mark.parametrize('queued',[False,True])
def test_failure_callback_starts_new_operation_without_late_signal_corruption(queued):
    first=Reply(b'x'*262145,queued=queued); following=sequence()
    manager=Manager([first]+following); client=PublicExomolProductHttp(manager=manager)
    results=[]
    def failed(*args):
        results.append(args); client.download(ENTRY,REQUEST,lambda *later: results.append(later))
    client.download(ENTRY,REQUEST,failed)
    first.finished.emit(); first.finished.emit()
    assert client.reply is following[0] and len(results)==1
    for reply in following: reply.finished.emit()
    assert len(results)==2 and results[1][0]==result()


class ProductHttp:
    def download(self,entry,request,callback): self.request=request; self.callback=callback
    def finish(self,error=None):
        callback,self.callback=self.callback,None
        callback(None if error else result(),error)
    def cancel(self):
        if getattr(self,'callback',None): self.finish('cancelled')


def select_supported(browser):
    browser.query.setText('CO2'); browser.search_button.click()
    index=next(i for i,e in enumerate(browser.entries) if supported_entry(e))
    browser.results.setCurrentRow(index)


def test_browser_download_display_and_cached_reopen_preserve_observation(tmp_path):
    window=ECASWindow(projects_dir=tmp_path/'projects',reference_cache_dir=tmp_path/'cache')
    try:
        source=DATA.parents[1]/'NASA/2026-10-27/feinstein-2023.tbl'
        window._import_csv_from_path(str(source)); observation=window.current_spectrum
        browser=window.reference_browser; browser.product_http=ProductHttp()
        select_supported(browser)
        assert browser.download_button.isEnabled()
        browser.download_button.click()
        assert browser.busy and not browser.search_button.isEnabled()
        browser.product_http.finish()
        assert browser.reference_table.rowCount()==11 and browser.current_reference==result()
        envelope=json.loads(Path(browser.cached.currentData()).read_text())
        assert envelope['catalogue_context']['version']==ENTRY.version
        assert envelope['catalogue_context']['dataset']=='UCL-4000'
        assert 'csrfmiddlewaretoken' not in json.dumps(envelope)
        assert 'csrftoken' not in json.dumps(envelope)
        assert window.current_spectrum is observation
    finally: window.close()
    reopened=MolecularReferenceBrowser(cache_root=tmp_path/'cache')
    try:
        assert reopened.product_http is None and reopened.cached.count()==1
        reopened.load_reference_button.click()
        assert reopened.reference_table.rowCount()==11 and reopened.current_reference==result()
        assert reopened.product_http is None and reopened.http is None
    finally: reopened.shutdown(); reopened.close()


def test_unsupported_selection_and_failed_replacement_do_not_corrupt_reference(tmp_path):
    http=ProductHttp(); browser=MolecularReferenceBrowser(cache_root=tmp_path,product_http=http)
    try:
        browser.query.setText('Water'); browser.search(); browser.results.setCurrentRow(0)
        assert not browser.download_button.isEnabled()
        select_supported(browser); browser.download_button.click(); http.finish()
        old=browser.current_reference
        browser.download_button.click(); browser.cancel_button.click()
        assert browser.current_reference is old and not browser.busy
        assert 'Previous displayed reference unchanged' in browser.status.text()
        path=Path(browser.cached.currentData()); path.write_bytes(b'invalid')
        browser.load_reference_button.click()
        assert browser.current_reference is old and 'Could not open' in browser.status.text()
    finally: browser.shutdown(); browser.close()
