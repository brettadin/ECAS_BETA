"""Dedicated anonymous Qt client for one fixed ExoMol metadata endpoint only."""
from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkReply, QNetworkRequest

from .exomol_catalogue import MAX_BYTES
from .exomol_catalogue_cache import CATALOGUE_URL


class PublicExomolCatalogueHttp(QObject):
    """Injected managers are exclusive-use test dependencies, never shared managers."""

    def __init__(self, parent=None, manager=None):
        super().__init__(parent)
        self.reply = None
        self.closed = False
        self.manager = manager if manager is not None else QNetworkAccessManager(self)
        self.manager.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        self.manager.authenticationRequired.connect(self._authentication)
        self.manager.proxyAuthenticationRequired.connect(self._proxy_authentication)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._timed_out)

    def _timed_out(self):
        self.cancel('Catalogue request timed out')

    def _authentication(self, reply, auth):
        if reply is self.reply:
            self.cancel('Authentication is unsupported')

    def _proxy_authentication(self, proxy, auth):
        self.cancel('Proxy authentication is unsupported')

    def get(self, callback):
        if self.closed:
            raise ValueError('Catalogue client is closed')
        if self.reply is not None:
            raise ValueError('A catalogue request is already active')
        request = QNetworkRequest(QUrl(CATALOGUE_URL))
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        for attr in (QNetworkRequest.Attribute.CookieLoadControlAttribute,
                     QNetworkRequest.Attribute.CookieSaveControlAttribute,
                     QNetworkRequest.Attribute.AuthenticationReuseAttribute):
            request.setAttribute(attr, QNetworkRequest.LoadControl.Manual)
        request.setRawHeader(b'Accept-Encoding', b'identity')
        request.setRawHeader(b'User-Agent', b'ECAS-reference-metadata/1.0')
        self.buffer, self.failure, self.callback = bytearray(), None, callback
        reply = self.manager.get(request)
        self.reply = reply
        reply.setReadBufferSize(65536)
        reply.readyRead.connect(lambda: self._read(reply))
        reply.finished.connect(lambda: self._finished(reply))
        self.timer.start(15000)

    def cancel(self, reason='Catalogue refresh cancelled'):
        if self.reply is not None:
            self.failure = reason
            self.reply.abort()

    def shutdown(self):
        if self.closed:
            return
        self.closed = True
        self.cancel('Catalogue client closed')
        self.timer.stop()
        self.manager.authenticationRequired.disconnect(self._authentication)
        self.manager.proxyAuthenticationRequired.disconnect(self._proxy_authentication)
        self.reply, self.callback = None, None
        self.deleteLater()

    def _read(self, reply):
        if self.reply is not reply or self.failure:
            return
        while reply.bytesAvailable():
            self.buffer.extend(bytes(reply.read(min(65536, MAX_BYTES+1-len(self.buffer)))))
            if len(self.buffer)>MAX_BYTES:
                self.cancel('Catalogue response exceeds 1 MiB')
                return

    def _finished(self, reply):
        if self.reply is not reply:
            return
        self._read(reply)
        if self.reply is not reply:
            return
        self.timer.stop()
        error = self.failure
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if not error and (reply.error() != QNetworkReply.NetworkError.NoError or status != 200):
            error = f'Catalogue request failed (HTTP {status}): {reply.errorString()}'
        callback, raw = self.callback, bytes(self.buffer)
        self.reply, self.callback = None, None
        self.buffer.clear()
        reply.deleteLater()
        callback(raw if not error else None, error)
