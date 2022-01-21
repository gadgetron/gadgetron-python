
import os
import socket
import logging

from . import connection




def wait_for_client_connection(port):

    sock = socket.socket(family=socket.AF_INET6)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.listen(0)
    conn, address = sock.accept()
    sock.close()

    logging.info(f"Accepted connection from client: {address}")

    return conn


def listen(port, handler, *args, **kwargs):
    """
    Listens on a given port and invokes the handler function with a connection and the provided args and kwargs
    :param port: Port on which to listen
    :param handler: Callable which takes a connection and the remaining args
    :param args:
    :param kwargs:
    """
    logging.debug(f"Starting external Python module '{handler.__name__}' in state: [PASSIVE]")
    logging.debug(f"Waiting for connection from client on port: {port}")

    storage_address = kwargs.get('storage_address', os.environ.get("GADGETRON_STORAGE_ADDRESS", None))

    with connection.Connection(wait_for_client_connection(port), storage_address) as conn:
        handler(conn, *args, **kwargs)
