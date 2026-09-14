"""A minimal local HTTPS-CONNECT forward proxy that allowlists destination
hostnames, used to give the sandboxed evaluated process a real, enforced
network policy: "model-service communication allowed, everything else
blocked."

Why this exists: benchmark/harness/sandbox.py's Seatbelt profile can only
express (remote ip "*") or (remote ip "localhost") as the host term in a
network-outbound rule -- confirmed by direct testing on this host
(sandbox-exec rejects any literal IP or hostname with "host must be * or
localhost in network address"). Arbitrary per-host allowlisting is
therefore NOT expressible at the OS-sandbox layer alone on this platform.

The fix: the sandbox allows outbound connections ONLY to
"localhost:<proxy_port>" (a token macOS's sandbox-exec does support), and
this proxy -- running OUTSIDE the sandbox, in the trusted parent process --
is the only thing actually allowed to reach the real network. It enforces
the hostname allowlist at the application layer via HTTP CONNECT tunneling.
The evaluated process is pointed at it via HTTPS_PROXY/HTTP_PROXY.

Limitation (documented, not hidden): this requires the evaluated CLI to
honor those proxy environment variables for its own network calls. That is
a live-execution property that cannot be verified without a real network
call to the target service -- see config.EXPERIMENT_PREFLIGHT_REQUIRED.
"""

import http.server
import socket
import socketserver
import threading


class _AllowlistProxyHandler(http.server.BaseHTTPRequestHandler):
    allowed_destinations = frozenset()  # set of (host, port) tuples; set by start_proxy() via a subclass
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass  # keep selftest output clean; nothing here is sensitive

    def do_CONNECT(self):
        host, _, port_s = self.path.partition(":")
        port = int(port_s or "443")
        # Exact (host, port) match required -- an allowlisted host on any
        # OTHER port (e.g. api.anthropic.com:22) is denied, not just any
        # non-allowlisted host.
        if (host, port) not in self.allowed_destinations:
            self.send_response(403, "Forbidden by egress allowlist")
            self.end_headers()
            self.connection.close()
            return

        try:
            upstream = socket.create_connection((host, port), timeout=10)
        except OSError as e:
            self.send_response(502, f"Bad Gateway: {e}")
            self.end_headers()
            return

        self.send_response(200, "Connection Established")
        self.end_headers()

        client = self.connection
        self._relay(client, upstream)

    @staticmethod
    def _relay(a, b):
        def pump(src, dst):
            try:
                while True:
                    data = src.recv(65536)
                    if not data:
                        break
                    dst.sendall(data)
            except OSError:
                pass
            finally:
                try:
                    dst.shutdown(socket.SHUT_WR)
                except OSError:
                    pass

        t1 = threading.Thread(target=pump, args=(a, b), daemon=True)
        t2 = threading.Thread(target=pump, args=(b, a), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    def do_GET(self):
        # Plain (non-CONNECT) HTTP requests are refused -- this proxy only
        # exists to tunnel HTTPS to allowlisted hosts.
        self.send_response(405, "Method Not Allowed")
        self.end_headers()


class _ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def start_proxy(allowed_destinations, bind_host="127.0.0.1", port=0):
    """Starts the allowlisting proxy in a background thread, bound to
    `bind_host:port` (port=0 picks a free ephemeral port). `allowed_destinations`
    is an iterable of (host, port) tuples -- an exact match is required, so
    an allowlisted host is NOT permitted on any other port. Returns
    (server, thread, actual_port). Call stop_proxy(server) to shut down."""
    handler_cls = type(
        "AllowlistProxyHandler",
        (_AllowlistProxyHandler,),
        {"allowed_destinations": frozenset(allowed_destinations)},
    )
    server = _ThreadingServer((bind_host, port), handler_cls)
    actual_port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, actual_port


def stop_proxy(server):
    server.shutdown()
    server.server_close()
