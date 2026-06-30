"""Port analysis helpers for detecting pseudo-open behavior."""

from __future__ import annotations

import socket
import ssl


def _safe_close(sock):
    if sock is None:
        return
    try:
        sock.close()
    except Exception:
        pass


def check_port_real_service(host, port, timeout=3):
    """Classify if a TCP port appears truly serviced or pseudo-open."""

    port = int(port)
    result = {
        "host": host,
        "port": port,
        "state": "unknown",
        "reason": "",
    }

    sock = None
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.settimeout(timeout)

        if port == 22:
            try:
                banner = sock.recv(1024).decode(errors="ignore").strip()
            except socket.timeout:
                banner = ""
                result["state"] = "pseudo-open"
                result["reason"] = "no_ssh_banner_timeout"
            except OSError:
                banner = ""
                result["state"] = "pseudo-open"
                result["reason"] = "no_ssh_banner_connection_closed"

            if result["state"] == "unknown":
                if banner.startswith("SSH-"):
                    result["state"] = "open"
                    result["reason"] = "ssh_banner_received"
                    result["banner"] = banner[:100]
                elif banner:
                    result["state"] = "open"
                    result["reason"] = "unexpected_banner_received"
                    result["banner"] = banner[:100]
                else:
                    result["state"] = "pseudo-open"
                    result["reason"] = "no_ssh_banner_connection_closed"

        elif port == 80:
            request = (
                f"HEAD / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            ).encode("ascii", errors="ignore")
            sock.sendall(request)
            try:
                response = sock.recv(1024).decode(errors="ignore")
            except socket.timeout:
                response = ""
                result["state"] = "filtered"
                result["reason"] = "http_response_timeout"
            except OSError:
                response = ""
                result["state"] = "pseudo-open"
                result["reason"] = "no_http_response_connection_closed"

            if result["state"] == "unknown":
                text = response.strip()
                if text:
                    first_line = (
                        text.splitlines()[0].strip() if text.splitlines() else text
                    )
                    if first_line.startswith("HTTP/") or " HTTP/" in first_line:
                        result["state"] = "open"
                        result["reason"] = "http_response_received"
                    else:
                        result["state"] = "open"
                        result["reason"] = "non_http_response_received"
                    result["banner"] = text[:100]
                else:
                    result["state"] = "pseudo-open"
                    result["reason"] = "no_http_response_connection_closed"

        elif port == 443:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            tls_sock = None
            try:
                tls_sock = context.wrap_socket(sock, server_hostname=host)
                tls_sock.settimeout(timeout)
                result["state"] = "open"
                result["reason"] = "tls_handshake_success"
            except socket.timeout:
                result["state"] = "filtered"
                result["reason"] = "tls_handshake_timeout"
            except ssl.SSLError as exc:
                msg = str(exc).lower()
                if any(
                    token in msg
                    for token in (
                        "wrong version number",
                        "unknown protocol",
                        "http request",
                        "plaintext",
                    )
                ):
                    result["state"] = "open"
                    result["reason"] = "tls_handshake_protocol_mismatch"
                elif any(
                    token in msg
                    for token in (
                        "eof occurred",
                        "unexpected eof",
                        "connection reset",
                        "handshake failure",
                    )
                ):
                    result["state"] = "pseudo-open"
                    result["reason"] = "tls_handshake_closed"
                else:
                    result["state"] = "filtered"
                    result["reason"] = f"tls_handshake_error:{exc}"
            except (ConnectionResetError, BrokenPipeError):
                result["state"] = "pseudo-open"
                result["reason"] = "tls_handshake_closed"
            finally:
                _safe_close(tls_sock)
                sock = None

        else:
            try:
                banner = sock.recv(1024).decode(errors="ignore").strip()
            except socket.timeout:
                banner = ""
                result["state"] = "filtered"
                result["reason"] = "no_service_banner_timeout"
            except OSError:
                banner = ""
                result["state"] = "pseudo-open"
                result["reason"] = "no_banner_connection_closed"

            if result["state"] == "unknown":
                if banner:
                    result["state"] = "open"
                    result["reason"] = "service_detected"
                    result["banner"] = banner[:100]
                else:
                    result["state"] = "pseudo-open"
                    result["reason"] = "no_banner_connection_closed"

    except ConnectionRefusedError:
        result["state"] = "closed"
        result["reason"] = "connection_refused"
    except OSError as exc:  # pragma: no cover - depends on socket backend
        msg = str(exc).lower()
        errno_value = getattr(exc, "errno", None)
        if errno_value == 111 or "connection refused" in msg:
            result["state"] = "closed"
            result["reason"] = "connection_refused"
        else:
            result["state"] = "filtered"
            result["reason"] = str(exc)
    except Exception as exc:  # pragma: no cover - behavior driven by socket backend
        result["state"] = "filtered"
        result["reason"] = str(exc)
    finally:
        _safe_close(sock)

    return result
