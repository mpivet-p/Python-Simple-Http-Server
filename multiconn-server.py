import selectors
import socket
import types
import sys

def accept_wrapper(sock: socket.socket, sel: selectors.DefaultSelector) -> None:
    conn, addr = sock.accept()
    print(f'Accepted connection from {addr}')

    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(
        sel: selectors.DefaultSelector, key: selectors.SelectorKey, mask: int
) -> None:
    sock = key.fileobj
    data = key.data

    # Ready to receive
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            print(f'Received data from {data.addr}: {recv_data}')
        else:
            print(f'Closing connection with {data.addr}')
            sel.unregister(sock)
            sock.close()
    # Ready to write
    if mask & selectors.EVENT_WRITE:
        pass
        # if data.outb:
        #     sent = sock.send(data.outb)
        #     data.outb = data.outb[sent:]


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

    lsock.bind((host, port))
    lsock.listen()
    print(f"Listening on {host}:{port}")

    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    wait_for_events(sel)

if __name__ == "__main__":
    main()