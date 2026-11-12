"""Optional OpenAI API client for NetMon's Chad analysis tab."""

from __future__ import annotations

import base64
import http.client
import json
import os
import queue
import socket
import threading
import time
import re
import urllib.error
import urllib.request
import zlib

from netmon.core.image_snapshot import (
    ImageSnapshot,
    attachment_snapshots,
    snapshot_image,
)

from .ai_analysis_service import CHAD_COMMAND_GUIDANCE

try:
    import requests
except Exception:  # pragma: no cover - depends on optional runtime dependency.
    requests = None


# JSON responses for at most 3200 output tokens fit comfortably within this cap.
_MAX_TRANSPORT_BYTES = 2 * 1024 * 1024
_MAX_RESPONSE_BYTES = 4 * 1024 * 1024
_MAX_ERROR_BYTES = 64 * 1024
_READ_CHUNK_BYTES = 16 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("API response deadline exceeded.")
    return remaining


def _arm_deadline(raw_socket, deadline, timers):
    # Keep our own TCP descriptor: TLS detaches the original socket, and a
    # TLS-in-TLS SSLTransport need not implement shutdown(). No wrapper internals.
    guard = socket.fromfd(
        raw_socket.fileno(), raw_socket.family, raw_socket.type, raw_socket.proto
    )

    def abort_read():
        try:
            guard.shutdown(socket.SHUT_RDWR)
        except OSError:
            # Already closed/unconnected. Every continuation checks the deadline.
            pass

    try:
        guard.settimeout(raw_socket.gettimeout())
        timer = threading.Timer(_remaining(deadline), abort_read)
        timer.daemon = True
        timer.start()
    except (OSError, RuntimeError):
        guard.close()
        raise
    timers.append((timer, guard))


def _connect_with_budget(
    address, deadline, timers, source_address=None, socket_options=()
):
    _remaining(deadline)
    addresses = socket.getaddrinfo(*address, 0, socket.SOCK_STREAM)
    _remaining(deadline)  # Never connect after a late system DNS result.
    last_error = None
    for family, kind, proto, _name, target in addresses:
        _remaining(deadline)
        sock = socket.socket(family, kind, proto)
        try:
            sock.settimeout(_remaining(deadline))
            if source_address:
                sock.bind(source_address)
            for option in socket_options or ():
                sock.setsockopt(*option)
            _arm_deadline(sock, deadline, timers)
            sock.connect(target)
            _remaining(deadline)
            return sock
        except OSError as exc:
            sock.close()
            last_error = exc
        except Exception:
            # Registration/provider failures must release the owned TCP socket.
            sock.close()
            raise
        _remaining(deadline)  # No retry against another address after expiry.
    if last_error is not None:
        raise last_error
    raise OSError("No address available for API request.")


def _connect_socks_with_budget(connection, deadline, timers):
    # Optional PySocks still owns protocol/authentication. Resolve locally only
    # when requested, then pin numeric addresses before its blocking connect.
    import socks

    options = connection._socks_options
    _remaining(deadline)
    addresses = socket.getaddrinfo(
        options["proxy_host"], options["proxy_port"], 0, socket.SOCK_STREAM
    )
    _remaining(deadline)
    targets = [connection.host]
    if not options["rdns"]:
        family = socket.AF_INET if options["socks_version"] == socks.SOCKS4 else 0
        targets = [
            address[4][0]
            for address in socket.getaddrinfo(
                connection.host, connection.port, family, socket.SOCK_STREAM
            )
        ]
        _remaining(deadline)

    class BudgetSocksSocket(socks.socksocket):
        # PySocks performs its handshake after TCP connect. In particular, a
        # late successful connect must not send even the first negotiation byte.
        def send(self, *args, **kwargs):
            _remaining(deadline)
            return super().send(*args, **kwargs)

        def sendall(self, *args, **kwargs):
            _remaining(deadline)
            return super().sendall(*args, **kwargs)

        def recv(self, *args, **kwargs):
            _remaining(deadline)
            result = super().recv(*args, **kwargs)
            _remaining(deadline)
            return result

        def recv_into(self, *args, **kwargs):
            _remaining(deadline)
            result = super().recv_into(*args, **kwargs)
            _remaining(deadline)
            return result

    last_error = None
    for family, kind, proto, _name, proxy_address in addresses:
        proxy_host = proxy_address[0]
        if family == socket.AF_INET6 and proxy_address[3]:
            proxy_host += f"%{proxy_address[3]}"
        for target in targets:
            _remaining(deadline)
            sock = BudgetSocksSocket(family, kind, proto)
            try:
                sock.set_proxy(
                    options["socks_version"],
                    proxy_host,
                    options["proxy_port"],
                    options["rdns"],
                    options["username"],
                    options["password"],
                )
                sock.settimeout(_remaining(deadline))
                if connection.source_address:
                    sock.bind(connection.source_address)
                for option in connection.socket_options or ():
                    sock.setsockopt(*option)
                _arm_deadline(sock, deadline, timers)
                _remaining(deadline)
                sock.connect((target, connection.port))
                _remaining(deadline)
                return sock
            except OSError as exc:
                sock.close()
                last_error = exc
            except Exception:
                # Optional provider failures must not retain the owned socket.
                sock.close()
                raise
            _remaining(deadline)
    if last_error is not None:
        raise last_error
    raise OSError("No address available for API SOCKS proxy request.")


def _budget_connection(base, deadline, timers, *, socks_proxy=False):
    class BudgetConnection(base):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # stdlib uses this instance attribute; urllib3 uses _new_conn.
            self._create_connection = (
                lambda address, timeout=None, source_address=None: _connect_with_budget(
                    address, deadline, timers, source_address
                )
            )

        def _new_conn(self):
            if socks_proxy:
                return _connect_socks_with_budget(self, deadline, timers)
            return _connect_with_budget(
                (getattr(self, "_dns_host", self.host), self.port),
                deadline,
                timers,
                self.source_address,
                self.socket_options,
            )

        def connect(self):
            _remaining(deadline)
            try:
                super().connect()
                _remaining(deadline)
            except (OSError, ValueError):
                self.close()
                raise

    return BudgetConnection


class _BudgetHTTPHandler(urllib.request.HTTPHandler):
    def __init__(self, connection):
        super().__init__()
        self.connection = connection

    def http_open(self, req):
        return self.do_open(self.connection, req)


class _BudgetHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, connection):
        super().__init__()
        self.connection = connection

    def https_open(self, req):
        return self.do_open(self.connection, req, context=self._context)


def _read_response(stream, headers, status, deadline):
    encoding = headers.get("Content-Encoding", "identity").strip().lower()
    if encoding not in ("identity", "gzip", "deflate"):
        raise ValueError("Unsupported API response Content-Encoding.")
    decoder = None
    if encoding != "identity":
        decoder = zlib.decompressobj(31 if encoding == "gzip" else 15)
    wire_limit = _MAX_TRANSPORT_BYTES if status == 200 else _MAX_ERROR_BYTES
    data_limit = _MAX_RESPONSE_BYTES if status == 200 else _MAX_ERROR_BYTES
    length = headers.get("Content-Length")
    if length is not None:
        if not length.isascii() or not length.isdecimal():
            raise ValueError("Invalid API response Content-Length.")
        # Compare as strings to avoid allocating enormous integers.
        normalized = length.lstrip("0") or "0"
        ceiling = str(wire_limit)
        if len(normalized) > len(ceiling) or (
            len(normalized) == len(ceiling) and normalized > ceiling
        ):
            raise ValueError("API response exceeds transport byte limit.")

    # read1 avoids filling an entire chunk; the connection watchdog interrupts
    # trickled chunk headers too, where idle timeouts reset on each recv.
    data = bytearray()
    received = 0
    while True:
        _remaining(deadline)
        chunk = stream.read1(min(_READ_CHUNK_BYTES, wire_limit + 1 - received))
        _remaining(deadline)
        if not chunk:
            if length is not None and received != int(length):
                raise ValueError("Incomplete API response body.")
            if decoder is not None and not decoder.eof:
                raise ValueError("Incomplete compressed API response.")
            return data.decode("utf-8", errors="replace")
        received += len(chunk)
        if received > wire_limit:
            raise ValueError("API response exceeds transport byte limit.")
        if decoder is None:
            data.extend(chunk)
            if len(data) > data_limit:
                raise ValueError("API response exceeds decoded byte limit.")
            continue
        pending = chunk
        while True:
            _remaining(deadline)
            decoded = decoder.decompress(
                pending, min(_READ_CHUNK_BYTES, data_limit + 1 - len(data))
            )
            if decoder.unused_data:
                raise ValueError("Trailing compressed API response data.")
            data.extend(decoded)
            if len(data) > data_limit:
                raise ValueError("API response exceeds decoded byte limit.")
            pending = decoder.unconsumed_tail
            if not pending:
                break


class AiOnlineService:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.default_model = "gpt-4.1-mini"
        self.last_usage = {}
        self.last_usage_text = ""
        self._http_lock = threading.Lock()
        self.last_response_incomplete = False

    def is_available(self):
        return bool(self.api_key)

    def image_to_data_url(self, image: ImageSnapshot | str) -> str:
        # Direct callers still get a bounded, no-follow read. Queued attachments
        # must already be snapshots; the payload builders never reopen paths.
        snapshot = image if isinstance(image, ImageSnapshot) else snapshot_image(image)
        data = base64.b64encode(snapshot.data).decode("ascii")
        return f"data:{snapshot.mime_type};base64,{data}"

    def _image_content_items(self, files: list[dict]) -> list[dict]:
        return [
            {
                "type": "input_image",
                "image_url": self.image_to_data_url(snapshot),
                "detail": "auto",
            }
            for snapshot in attachment_snapshots(files)
        ]

    def _post_json(self, url: str, headers: dict, payload: dict, timeout: int):
        deadline = time.monotonic() + timeout
        _remaining(deadline)
        # System DNS cannot be cancelled portably. Bound the caller and permit
        # at most one outstanding transport per service until DNS really exits.
        if not self._http_lock.acquire(blocking=False):
            raise TimeoutError("Previous API request is still finishing.")
        results = queue.Queue(maxsize=1)

        def run():
            try:
                outcome = (
                    True,
                    self._post_json_transport(url, headers, payload, deadline),
                )
            # Forward transport failures across the worker boundary.
            except Exception as exc:  # noqa: BLE001
                outcome = (False, exc)
            finally:
                self._http_lock.release()
            results.put(outcome)

        worker = threading.Thread(target=run, daemon=True)
        try:
            worker.start()
        except RuntimeError:
            self._http_lock.release()
            raise
        try:
            success, result = results.get(timeout=_remaining(deadline))
        except queue.Empty as exc:
            raise TimeoutError("API response deadline exceeded.") from exc
        _remaining(deadline)
        if not success:
            raise result
        return result

    def _post_json_transport(self, url, headers, payload, deadline):
        timers = []
        try:
            return self._post_json_with_budget(url, headers, payload, deadline, timers)
        except Exception as exc:
            if time.monotonic() >= deadline or isinstance(
                exc, (TimeoutError, socket.timeout)
            ):
                raise TimeoutError("API response deadline exceeded.") from exc
            raise
        finally:
            for timer, guard in timers:
                timer.cancel()
                timer.join()
                guard.close()

    def _post_json_with_budget(self, url, headers, payload, deadline, timers):
        headers = {**headers, "Accept-Encoding": "identity"}
        if requests is not None:
            # Use scoped pool classes; do not alter global urllib3 state.
            from urllib3 import connectionpool

            class HTTPPool(connectionpool.HTTPConnectionPool):
                ConnectionCls = _budget_connection(
                    connectionpool.HTTPConnectionPool.ConnectionCls, deadline, timers
                )

            class HTTPSPool(connectionpool.HTTPSConnectionPool):
                ConnectionCls = _budget_connection(
                    connectionpool.HTTPSConnectionPool.ConnectionCls, deadline, timers
                )

            class BudgetAdapter(requests.adapters.HTTPAdapter):
                def init_poolmanager(self, *args, **kwargs):
                    super().init_poolmanager(*args, **kwargs)
                    self.poolmanager.pool_classes_by_scheme = {
                        "http": HTTPPool,
                        "https": HTTPSPool,
                    }

                def proxy_manager_for(self, proxy, **kwargs):
                    manager = super().proxy_manager_for(proxy, **kwargs)
                    # Preserve the selected native pools, especially SOCKS pools.
                    # Only their connection factory gains the same budget.
                    socks_proxy = hasattr(manager, "proxy_url")
                    if proxy.lower().startswith(
                        ("socks4:", "socks4a:", "socks5:", "socks5h:")
                    ) and not (
                        socks_proxy
                        or getattr(getattr(manager, "proxy", None), "scheme", None)
                        in {"http", "https"}
                    ):
                        raise ValueError(
                            "Unsupported SOCKS proxy manager; no fallback."
                        )
                    pools = {}
                    for scheme, pool in manager.pool_classes_by_scheme.items():

                        class BudgetPool(pool):
                            ConnectionCls = _budget_connection(
                                pool.ConnectionCls,
                                deadline,
                                timers,
                                socks_proxy=socks_proxy,
                            )

                        pools[scheme] = BudgetPool
                    manager.pool_classes_by_scheme = pools
                    return manager

            # Session.send consumes redirect bodies even with allow_redirects=False
            # while preparing Response.next. Suppress that preparation as well.
            with requests.Session() as session:
                session.mount("http://", BudgetAdapter())
                session.mount("https://", BudgetAdapter())
                session.resolve_redirects = lambda *args, **kwargs: iter(())
                with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=_remaining(deadline),
                    stream=True,
                    allow_redirects=False,
                ) as response:
                    _remaining(deadline)
                    raw = response.raw
                    raw.decode_content = False
                    return response.status_code, _read_response(
                        # read1 is public in recent urllib3. Older supported
                        # versions need the stdlib reader as a narrow fallback.
                        raw if callable(getattr(raw, "read1", None)) else raw._fp,
                        response.headers,
                        response.status_code,
                        deadline,
                    )

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        opener = urllib.request.build_opener(
            _NoRedirect(),
            _BudgetHTTPHandler(
                _budget_connection(http.client.HTTPConnection, deadline, timers)
            ),
            _BudgetHTTPSHandler(
                _budget_connection(http.client.HTTPSConnection, deadline, timers)
            ),
        )
        try:
            response = opener.open(req, timeout=_remaining(deadline))
        except urllib.error.HTTPError as exc:
            # HTTPError wraps the actual HTTPResponse one level deeper.
            with exc:
                return exc.code, _read_response(
                    exc.fp,
                    exc.headers,
                    exc.code,
                    deadline,
                )
        with response:
            _remaining(deadline)
            return response.code, _read_response(
                response,
                response.headers,
                response.code,
                deadline,
            )

    def _update_usage_from_response(self, data: dict):
        usage = data.get("usage") or {}
        if not isinstance(usage, dict):
            self.last_usage = {}
            self.last_usage_text = ""
            return

        self.last_usage = dict(usage)
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        total_tokens = int(
            usage.get("total_tokens") or (input_tokens + output_tokens) or 0
        )
        if total_tokens <= 0:
            self.last_usage_text = ""
            return
        self.last_usage_text = (
            f"Gesamt: {total_tokens} | Input: {input_tokens} | Output: {output_tokens}"
        )

    def _safe_error_text(self, text: str, *, limit: int | None = 1000) -> str:
        text = str(text)
        if self.api_key:
            text = text.replace(self.api_key, "[REDACTED]")
        text = re.sub(r"(?i)\bBearer\s+\S+", "Bearer [REDACTED]", text)
        text = re.sub(r"\bsk-[A-Za-z0-9_*.-]{4,}", "[REDACTED]", text)
        return text if limit is None else text[:limit]

    def _format_api_error(
        self, response_text: str, status_code: int | None = None
    ) -> str:
        try:
            data = json.loads(response_text)
        except (ValueError, TypeError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        error = data.get("error")
        if not isinstance(error, dict):
            error = data
        message = error.get("message")
        if not isinstance(message, str) or not message.strip():
            message = "Unbekannter API-Fehler"
        parts = ["Fehler: " + self._safe_error_text(message.strip())]
        if type(status_code) is int and 100 <= status_code <= 599:
            parts.append(f"HTTP-Status: {status_code}")
        for key, label in (("code", "API-Code"), ("type", "API-Typ")):
            value = error.get(key)
            if isinstance(value, str):
                value = self._safe_error_text(value)
                if re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", value):
                    parts.append(f"{label}: {value}")
        if status_code == 401:
            parts.append(
                "Anmeldung abgelehnt: OpenAI-API-Key, Projektberechtigungen und gegebenenfalls IP-Freigabe prüfen. "
                "Speichern im Schlüsselbund bestätigt keine erfolgreiche API-Anmeldung."
            )
        return "\n".join(parts)

    def _analysis_max_output_tokens(
        self, prompt: str, files: list[dict] | None = None
    ) -> int:
        prompt_length = len(str(prompt or ""))
        if prompt_length >= 80000:
            return 6400
        if prompt_length >= 40000:
            return 5120
        return 4096

    def _analysis_timeout_seconds(
        self, prompt: str, files: list[dict] | None = None
    ) -> int:
        prompt_length = len(str(prompt or ""))
        has_files = bool(files)
        if prompt_length >= 80000 or has_files:
            return 90
        if prompt_length >= 40000:
            return 75
        if prompt_length >= 15000:
            return 60
        return 60

    def _read_response(self, data: dict) -> tuple[bool, str]:
        """Preserve partial output, but never report it as a completed answer."""
        self._update_usage_from_response(data)
        self.last_response_incomplete = data.get("status") == "incomplete"
        text = data.get("output_text")
        if not isinstance(text, str) or not text.strip():
            parts = []
            for item in data.get("output", []) or []:
                for content in item.get("content", []) or []:
                    if content.get("type") == "output_text":
                        parts.append(content.get("text", ""))
            text = "\n".join(parts)
        text = text.strip()
        if self.last_response_incomplete:
            details = data.get("incomplete_details")
            reason = details.get("reason") if isinstance(details, dict) else None
            if reason == "max_output_tokens":
                notice = "Antwort unvollständig: Ausgabelimit erreicht."
            elif reason == "content_filter":
                notice = (
                    "Antwort unvollständig: API-Inhaltsfilter hat die Ausgabe begrenzt."
                )
            else:
                notice = "Antwort unvollständig: Die API meldet einen Abbruch."
            notice += "\nDer folgende Text ist nur eine Teilantwort. Es erfolgt keine automatische Wiederholung."
            if text:
                notice += "\n\n" + self._safe_error_text(text, limit=None)
            return False, notice
        if data.get("status") in {"failed", "cancelled", "queued", "in_progress"}:
            return False, "Antwort nicht abgeschlossen.\n" + self._format_api_error(
                data.get("error") and json.dumps({"error": data["error"]}) or "{}"
            )
        if not text:
            return False, "Empty response from API."
        return True, text

    def analyze(self, prompt: str, files: list[dict] | None = None) -> tuple[bool, str]:
        self.last_response_incomplete = False
        if not self.api_key:
            return False, "No API key configured (OPENAI_API_KEY)."

        try:
            url = "https://api.openai.com/v1/responses"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            files = files or []
            max_output_tokens = self._analysis_max_output_tokens(prompt, files)
            timeout_seconds = self._analysis_timeout_seconds(prompt, files)
            if files:
                content_items = [{"type": "input_text", "text": prompt}]
                content_items.extend(self._image_content_items(files))
                payload = {
                    "model": self.default_model,
                    "input": [{"role": "user", "content": content_items}],
                    "max_output_tokens": max_output_tokens,
                }
            else:
                payload = {
                    "model": self.default_model,
                    "input": prompt,
                    "max_output_tokens": max_output_tokens,
                }

            payload["instructions"] = CHAD_COMMAND_GUIDANCE
            status_code, response_text = self._post_json(
                url,
                headers,
                payload,
                timeout=timeout_seconds,
            )

            if status_code != 200:
                return False, self._format_api_error(response_text, status_code)

            data = json.loads(response_text)
            return self._read_response(data)

        except Exception as exc:
            return False, "Error during online analysis: " + self._safe_error_text(exc)

    def chat(
        self, messages: list[dict], files: list[dict] | None = None
    ) -> tuple[bool, str]:
        self.last_response_incomplete = False
        if not self.api_key:
            return False, "No API key configured."

        try:
            url = "https://api.openai.com/v1/responses"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            input_items = [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Du bist Chad, der NetMon Analyse-Assistent. "
                                "Antworte auf Deutsch, verständlich, praktisch und "
                                "sicherheitsbewusst. Gib bei Netzwerk-, Firewall-, "
                                "DNS-, VPN- und Linux-Themen konkrete nächste Schritte. "
                                "Keine gefährlichen Befehle ohne Warnung."
                            ),
                        }
                    ],
                }
            ]

            recent_messages = (messages or [])[-12:]
            files = files or []
            image_items = self._image_content_items(files)
            last_user_index = -1
            for idx, msg in enumerate(recent_messages):
                if msg.get("role", "user") == "user":
                    last_user_index = idx

            for idx, msg in enumerate(recent_messages):
                role = msg.get("role", "user")
                text = (msg.get("content") or "").strip()
                if not text:
                    continue

                if role == "assistant":
                    input_items.append(
                        {
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": text}],
                        }
                    )
                else:
                    if role not in ("user", "developer", "system"):
                        role = "user"

                    content_items = [{"type": "input_text", "text": text}]
                    if role == "user" and idx == last_user_index:
                        content_items.extend(image_items)

                    input_items.append(
                        {
                            "role": role,
                            "content": content_items,
                        }
                    )

            payload = {
                "model": self.default_model,
                "input": input_items,
                "instructions": CHAD_COMMAND_GUIDANCE,
                "max_output_tokens": 900,
            }

            status_code, response_text = self._post_json(
                url,
                headers,
                payload,
                timeout=30,
            )

            if status_code != 200:
                return False, self._format_api_error(response_text, status_code)

            data = json.loads(response_text)
            return self._read_response(data)

        except Exception as exc:
            return False, "Error in chat: " + self._safe_error_text(exc)


__all__ = ["AiOnlineService"]
