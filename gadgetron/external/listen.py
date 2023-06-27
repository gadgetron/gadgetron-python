
import logging

import socket

from . import connection


def wait_for_client_connection(port, use_ipv4):
    if use_ipv4:
        sock = socket.socket(family=socket.AF_INET)
    else:
        sock = socket.socket(family=socket.AF_INET6)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.listen(0)
    conn, address = sock.accept()

    logging.info(f"Accepted connection from client: {address}")

    return conn


def listen(port, handler, use_ipv4=False, *args, **kwargs):
    """
    Listens on a given port and invokes the handler function with a connection and the provided args and kwargs
    :param port: Port on which to listen
    :param handler: Callable which takes a connection and the remaining args
    :param args:
    :param kwargs:
    """
    logging.debug(f"Starting external Python module '{handler.__name__}' in state: [PASSIVE]")
    logging.debug(f"Waiting for connection from client on port: {port}")

    with connection.Connection(wait_for_client_connection(port, use_ipv4=use_ipv4)) as conn:
        handler(conn, *args, **kwargs)
