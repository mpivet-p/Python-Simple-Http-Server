import socket
import selectors
import types
import sys

def start_connections(sel: selectors.DefaultSelector, host: str, port: int, num_conns: int) -> None:
    messages = [b'Message 1 from client.', b'Message 2 from client.']
    msgs_length = sum(len(m) for m in messages)

    for i in range(0, num_conns):
        connid = i + 1
        print(f"Starting connection #{connid} to {host}:{port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex((host, port))

        events = selectors.EVENT_WRITE

        data = types.SimpleNamespace(
            connid=connid, msg_total=msgs_length, recv_total=0, messages=list(messages), outb=b""
        )
        sel.register(sock, events, data=data)


def service_connection(sel: selectors.DefaultSelector, key: selectors.SelectorKey, mask: int) -> None:
    sock = key.fileobj
    data = key.data

    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        if data.outb:
            print(f"Sending {data.outb!r} to connection #{data.connid}")
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]
        elif not data.messages:
            print(f"Closing connection #{data.connid}")
            sel.unregister(sock)
            sock.close()


def wait_for_events(sel: selectors.DefaultSelector) -> None:
    try:
        while True:
            events = sel.select(timeout=1)
            if events:
                for key, mask in events:
                    service_connection(sel, key, mask)

            if not sel.get_map() or not events:
                break
    except KeyboardInterrupt:
        print("Keyboard interrupt caught -> exiting...")
    finally:
        sel.close()

def main() -> None:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)

    sel = selectors.DefaultSelector()

    start_connections(sel, sys.argv[1], int(sys.argv[2]), 2)
    wait_for_events(sel)

if __name__ == "__main__":
    main()