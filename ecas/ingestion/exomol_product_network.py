"""Anonymous, same-origin three-step reference request with ephemeral CSRF state."""
from dataclasses import dataclass
import re

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkReply, QNetworkRequest, QNetworkCookie

from .exomol_product import ORIGIN, SERVICE_URL, ProductRequest, parse_form, product_url, supported_entry, validate_product


@dataclass(frozen=True)
class RetrievedCrossSection:
    request: ProductRequest
    raw: bytes
    product: object


class PublicExomolProductHttp(QObject):
    """One active operation; injected managers must be exclusive-use dependencies."""
    phaseChanged = Signal(str)

    def __init__(self, parent=None, manager=None):
        super().__init__(parent)
        self.manager=manager if manager is not None else QNetworkAccessManager(self)
        self.manager.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        self.manager.authenticationRequired.connect(self._authentication)
        self.manager.proxyAuthenticationRequired.connect(self._proxy_authentication)
        self.timer=QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._timeout)
        self.reply=None; self.callback=None; self.closed=False; self.request=None

    def _authentication(self, reply, auth):
        if reply is self.reply: self.cancel('Account authentication is unsupported')

    def _proxy_authentication(self, proxy, auth): self.cancel('Proxy authentication is unsupported')
    def _timeout(self): self.cancel('Reference request timed out')

    def download(self, entry, request, callback):
        if self.closed or self.callback is not None:
            raise ValueError('Reference client is closed or already active')
        if not supported_entry(entry) or not isinstance(request,ProductRequest):
            raise ValueError('Retrieval is supported only for CO2 / 12C-16O2 / UCL-4000')
        self.request=request; self.callback=callback
        self.timer.start(30000)  # Overall deadline for form, POST and product GET.
        try: self._send('form','GET',SERVICE_URL)
        except Exception as error: self._complete(None,str(error) or 'Could not start reference request')

    def _send(self, phase, method, url, body=None, cookie=None):
        allowed=SERVICE_URL if phase in ('form','submit') else ORIGIN+self.request.product_path
        if url!=allowed or method!=('POST' if phase=='submit' else 'GET'):
            raise ValueError('Unsupported reference endpoint')
        self.phase=phase
        self.phaseChanged.emit({'form':'Reading reference request form…','submit':'Requesting the selected cross section…',
                                'product':'Downloading the calculated cross section…'}[phase])
        if self.callback is None: return
        request=QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        for attr in (QNetworkRequest.Attribute.CookieLoadControlAttribute,QNetworkRequest.Attribute.CookieSaveControlAttribute,
                     QNetworkRequest.Attribute.AuthenticationReuseAttribute):
            request.setAttribute(attr,QNetworkRequest.LoadControl.Manual)
        request.setRawHeader(b'Accept-Encoding',b'identity')
        request.setRawHeader(b'User-Agent',b'ECAS-reference-products/1.0')
        self.buffer=bytearray()
        if method=='POST':
            request.setRawHeader(b'Cookie',cookie)
            request.setRawHeader(b'Referer',SERVICE_URL.encode())
            request.setRawHeader(b'Origin',ORIGIN.encode())
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader,'application/x-www-form-urlencoded')
            reply=self.manager.post(request,body)
        else: reply=self.manager.get(request)
        self.reply=reply
        reply.setReadBufferSize(65536)
        reply.readyRead.connect(lambda: self._read(reply))
        reply.finished.connect(lambda: self._finished(reply))

    def _read(self, reply):
        if self.reply is not reply: return
        limit=1048576 if self.phase=='product' else 262144
        while reply.bytesAvailable():
            self.buffer.extend(bytes(reply.read(min(65536,limit+1-len(self.buffer)))))
            if len(self.buffer)>limit:
                self.cancel('Reference response exceeds its size limit')
                return

    def _finished(self, reply):
        if self.reply is not reply: return
        self._read(reply)
        if self.reply is not reply: return
        self.reply=None
        raw=bytes(self.buffer); self.buffer.clear()
        completed_product=None
        try:
            status=reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if reply.error()!=QNetworkReply.NetworkError.NoError or status!=200:
                raise ValueError(f'Reference request failed (HTTP {status}): {reply.errorString()}')
            if self.phase=='form':
                form=parse_form(raw)
                cookies=[]
                for name,value in reply.rawHeaderPairs():
                    if bytes(name).lower()==b'set-cookie':
                        cookies.extend(c for c in QNetworkCookie.parseCookies(value) if bytes(c.name())==b'csrftoken')
                if len(cookies)!=1 or not re.fullmatch(b'[A-Za-z0-9]{32,128}',bytes(cookies[0].value())):
                    raise ValueError('Anonymous anti-forgery cookie is missing or ambiguous')
                # Only this fresh anonymous cookie is sent, and only to this form POST.
                self._send('submit','POST',SERVICE_URL,form.body(self.request),b'csrftoken='+bytes(cookies[0].value()))
            elif self.phase=='submit':
                self._send('product','GET',product_url(raw,self.request))
            else:
                product=validate_product(raw,self.request)
                completed_product=RetrievedCrossSection(self.request,raw,product)
        except Exception as error:
            self._complete(None,str(error) or 'Reference response could not be validated')
        finally: reply.deleteLater()
        # Call application code outside the parsing exception handler. A callback
        # that starts a new operation must never have that operation cancelled by
        # an exception attributed to the already completed request.
        if completed_product is not None: self._complete(completed_product,None)

    def cancel(self, reason='Reference request cancelled'):
        self._complete(None,reason)

    def _complete(self, result, error):
        callback,self.callback=self.callback,None
        reply,self.reply=self.reply,None
        self.timer.stop()
        self.request=None
        if hasattr(self,'buffer'): self.buffer.clear()
        if reply is not None:
            reply.abort()
            reply.deleteLater()
        if callback is not None: callback(result,error)

    def shutdown(self):
        if self.closed: return
        self.closed=True
        self.cancel('Reference client closed')
        self.manager.authenticationRequired.disconnect(self._authentication)
        self.manager.proxyAuthenticationRequired.disconnect(self._proxy_authentication)
        self.deleteLater()
