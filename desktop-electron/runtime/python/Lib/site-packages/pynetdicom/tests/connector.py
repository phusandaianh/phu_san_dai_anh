import socket
from struct import pack
import time


def create_socket(address):
    # AF_INET: IPv4, SOCK_STREAM: TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # SO_REUSEADDR: reuse the socket in TIME_WAIT state without
    #   waiting for its natural timeout to expire
    #   Allows local address reuse
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # If no timeout is set then recv() will block forever if
    #   the connection is kept alive with no data sent
    # SO_RCVTIMEO: the timeout on receive calls in seconds
    #   set using a packed binary string containing two uint32s as
    #   (seconds, microseconds)
    # if self.assoc.network_timeout is not None:
    timeout_seconds = 5
    timeout_microsec = 5 % 1 * 1000
    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_RCVTIMEO,
        pack("ll", timeout_seconds, timeout_microsec),
    )

    sock.bind(address)

    return sock


if __name__ == "__main__":
    for ii in range(60):
        sock = create_socket(("localhost", 0))
        sock.connect(("localhost", 11112))
        sock.settimeout(None)

        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        sock.close()

        time.sleep(10)
