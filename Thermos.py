import socket
import selectors
import types
from HttpRequest import HttpRequest
from HttpResponse import HttpResponse
from _collections_abc import Callable

class Thermos:

    _server_name: str
    _selector: selectors.DefaultSelector
    _socket: socket.socket
    _host: str
    _port: int
    _routes: dict

    def __init__(self, name: str) -> None:
        self._server_name = name
        self._routes = {"GET": dict()}


    def run(self, host: str = "0.0.0.0", port: int = 5000) -> None:
        print(self._routes)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._selector = selectors.DefaultSelector()
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((host, port))
        self._socket.listen()

        print(f"Listening on {host}:{port}")

        self._socket.setblocking(False)
        self._selector.register(self._socket, selectors.EVENT_READ, data=None)

        self._events_loop()


    def route(self, route: str, methods: list[str] = ["GET"]) -> Callable:
        def decorator(func: Callable) -> Callable:
            print(f"I am the decorator {func=}, {route=}, {methods=}")
            self._add_route(route, methods, func)
        return decorator


    def _add_route(self, route: str, methods: list[str], func: Callable) -> None:
        for mtd in methods:
            self._routes[mtd][route] = func


    def _accept_wrapper(self, sock: socket.socket) -> None:
        conn, addr = sock.accept()
        print(f'Accepted connection from {addr}') # Debug

        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", send_and_close=False)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self._selector.register(conn, events, data=data)


    def _events_loop(self) -> None:
        try:
            while True:
                events = self._selector.select(timeout=None)

                for key, mask in events:
                    if key.data is None:
                        self._accept_wrapper(key.fileobj)
                    else:
                        self._service_connection(key, mask)

        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self._selector.close()


    def _service_connection(
            self, key: selectors.SelectorKey, mask: int
    ) -> None:
        sock: socket.socket = key.fileobj
        data = key.data

        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(2048)
            if recv_data:
                data.inb += recv_data
                if HttpRequest.is_tls_handshake(data.inb):
                    self._reject_https_request(data)
                elif HttpRequest.is_http_request_complete(data.inb):
                    self._handle_http_request(data)
                else:
                    print("Unknown or incomplete request.")
            else:
                print(f'[]Closing connection with {data.addr}') # Debug
                self._selector.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                sent = sock.send(data.outb)
                data.outb = data.outb[sent:]
            if not data.outb and data.send_and_close:
                print(f"Closing connection with {data.addr}") # Debug
                self._selector.unregister(sock)
                sock.close()

    def _bad_request_handler(self, data: types.SimpleNamespace) -> None:
        response = HttpResponse(400, "Bad Request", {}, "400 Bad Request")
        data.outb = response.to_bytes()
        data.send_and_close = True

    def _not_found_handler(self, data: types.SimpleNamespace) -> None:
        response = HttpResponse(404, "Page Not Found", {}, "404 Page Not Found")
        data.outb = response.to_bytes()
        data.send_and_close = True

    def _handle_route(self, request: HttpRequest, data: types.SimpleNamespace) -> None:
        func = self._routes[request.method][request.path]
        ret = func()

        if type(ret) == str:
            response = HttpResponse(200, "OK", {}, ret)
        elif type(ret) == HttpResponse:
            response = ret
        else:
            response = HttpResponse(500, "Internal Server Error")

        data.outb = response.to_bytes()
        data.send_and_close = True


    def _handle_http_request(self, data: types.SimpleNamespace) -> None:
        if not HttpRequest.is_version_supported(data.inb):
            response = HttpResponse(505, "HTTP Version Not Supported", {}, "505 HTTP Version Not Supported")
            data.outb = response.to_bytes()
            data.send_and_close = True
            return
        
        request = HttpRequest(data.inb)

        if not request.method in self._routes:
            return self._bad_request_handler(data)
        if not request.path in self._routes[request.method]:
            return self._not_found_handler(data)
        
        self._handle_route(request, data)

    def _reject_https_request(self, data: types.SimpleNamespace) -> None:
        response = HttpResponse(
            400,
            "Bad Request",
            {
                "Content-Type": "text/plain",
                "Content-Length": "35",
                "Connection": "close"
            },
            "This server does not support HTTPS."
            )
        data.outb = response.to_bytes()
        data.send_and_close = True