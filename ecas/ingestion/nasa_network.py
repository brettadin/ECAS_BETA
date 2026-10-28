"""Asynchronous anonymous NASA-only HTTP with cancellation and bounded capture."""
from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkReply, QNetworkRequest

from .nasa_archive import allowed_url, MAX_BYTES


class PublicNasaHttp(QObject):
    """One active request on a dedicated manager.

    An injected manager is an exclusive-use dependency (primarily for testing),
    not a shared application manager. It is configured with NoProxy and must
    outlive this client. Sharing proxy/authentication state is unsupported.
    """

    def __init__(self, parent=None, manager=None):
        super().__init__(parent)
        self.reply = None
        self.manager = manager if manager is not None else QNetworkAccessManager(self)
        self.manager.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        self.manager.authenticationRequired.connect(self._authentication_required)
        self.manager.proxyAuthenticationRequired.connect(self._proxy_authentication_required)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.cancel("NASA request timed out"))

    def _authentication_required(self, reply, auth):
        if reply is self.reply:
            self.cancel("Authentication is unsupported")

    def _proxy_authentication_required(self, proxy, auth):
        self.cancel("Proxy authentication is unsupported")

    def get(self, url, callback):
        if self.reply is not None:
            raise ValueError("A NASA request is already active")
        if not allowed_url(url):
            raise ValueError("Unsupported NASA URL")
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        for attr in (QNetworkRequest.Attribute.CookieLoadControlAttribute,
                     QNetworkRequest.Attribute.CookieSaveControlAttribute,
                     QNetworkRequest.Attribute.AuthenticationReuseAttribute):
            request.setAttribute(attr, QNetworkRequest.LoadControl.Manual)
        request.setRawHeader(b"Accept-Encoding", b"identity")
        request.setRawHeader(b"User-Agent", b"ECAS-NASA-discovery/1.0")
        self.buffer = bytearray()
        self.failure = None
        self.callback = callback
        reply = self.manager.get(request)
        self.reply = reply
        reply.setReadBufferSize(65536)
        # Bind signals to their request, not whichever request is active later.
        reply.readyRead.connect(lambda: self._read(reply))
        reply.finished.connect(lambda: self._finished(reply))
        self.timer.start(15000)  # Overall request deadline, including DNS/connect.

    def cancel(self, reason="NASA request cancelled"):
        if self.reply is not None:
            self.failure = reason
            self.reply.abort()

    def _read(self, reply):
        if self.reply is not reply or self.failure:
            return
        while reply.bytesAvailable():
            self.buffer.extend(bytes(reply.read(min(65536, MAX_BYTES + 1 - len(self.buffer)))))
            if len(self.buffer) > MAX_BYTES:
                self.cancel("NASA response exceeds 1 MiB")
                return

    def _finished(self, reply):
        if self.reply is not reply:
            return
        self._read(reply)
        # A final drain can overflow and abort. abort() may synchronously emit
        # finished again, whose callback can already have started a new request.
        if self.reply is not reply:
            return
        self.timer.stop()
        error = self.failure
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if not error and (reply.error() != QNetworkReply.NetworkError.NoError or status != 200):
            error = f"NASA request failed (HTTP {status}): {reply.errorString()}"
        callback, raw = self.callback, bytes(self.buffer)
        self.reply = None
        self.callback = None
        self.buffer.clear()
        reply.deleteLater()
        callback(raw if not error else None, error)
