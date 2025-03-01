import selectors
import socket
import types
import sys
from HttpRequest import HttpRequest
from HttpResponse import HttpResponse


def accept_wrapper(sock: socket.socket, sel: selectors.DefaultSelector) -> None:
    conn, addr = sock.accept()
    print(f'Accepted connection from {addr}')

    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", send_and_close=False)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def handle_http_request(data: types.SimpleNamespace) -> None:
    if not HttpRequest.is_version_supported(data.inb):
        response = HttpResponse(505, "HTTP Version Not Supported", {}, "505 HTTP Version Not Supported")
        data.outb = response.to_bytes()
        data.send_and_close = True
        return
    
    request = HttpRequest(data.inb)
    # Temporary
    if request.path == "/":
        response = HttpResponse(200, "OK", {}, "Hi")
        data.outb = response.to_bytes()
        data.send_and_close = True
        return
    elif request.method == "GET":
        response = HttpResponse(404, "Page Not Found")
        data.outb = response.to_bytes()
        data.send_and_close = True
        return


def handle_https_request(data: types.SimpleNamespace) -> None:
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


def service_connection(
        sel: selectors.DefaultSelector, key: selectors.SelectorKey, mask: int
) -> None:
    sock: socket.socket = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(2048)
        if recv_data:
            data.inb += recv_data
            if HttpRequest.is_tls_handshake(data.inb):
                handle_https_request(data)
            elif HttpRequest.is_http_request_complete(data.inb):
                handle_http_request(data)
            else:
                print("Unknown or incomplete request.")

            # elif HttpRequest.is_request_supported(recv_data):
            #     request = HttpRequest(recv_data)
            # else:
            #     response = HttpResponse(505, "HTTP Version Not Supported", {}, "505 HTTP Version Not Supported")
            #     data.outb = response.to_bytes()
            #     data.send_and_close = True
        else:
            print(f'[]Closing connection with {data.addr}')
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            sent = sock.send(data.outb)
            # print(data.outb[:sent])
            data.outb = data.outb[sent:]
        if not data.outb and data.send_and_close:
            print(f"Closing connection with {data.addr}")
            sel.unregister(sock)
            sock.close()


def wait_for_events(sel: selectors.DefaultSelector) -> None:
    try:
        while True:
            events = sel.select(timeout=None)

            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj, sel)
                else:
                    service_connection(sel, key, mask)

    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        sel.close()

def main() -> None:
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "<host> <port>")
        return

    host, port = sys.argv[1], int(sys.argv[2])

    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sel = selectors.DefaultSelector()
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.bind((host, port))
    lsock.listen()
    print(f"Listening on {host}:{port}")

    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    wait_for_events(sel)

if __name__ == "__main__":
    main()