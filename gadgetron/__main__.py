
import os
import sys
import socket
import inspect
import logging

from typing import Callable

from .version import version
from .external import connection


def load_target(args) -> Callable[[connection.Connection], None]:

    module = __import__(args.get('module'), globals(), locals(), [args.get('target')], 0)
    target = getattr(module, args.get('target'), None)

    if inspect.isclass(target):
        return lambda conn: target().handle(conn)

    if callable(target):
        return target

    raise TypeError(f"Unable to initialize suitable target using symbol '{args.get('target')}'")


def main(args=None):

    if not args:
        return print(f"Gadgetron External Python Module v. {version}")

    args = dict(zip(['port', 'module', 'target'], args))

    logging.basicConfig(format=f"%(asctime)s.%(msecs)03d %(levelname)s " +
                               f"[ext. %(process)d {args.get('module')}.{args.get('target')}] %(message)s",
                        level=logging.getLevelName(os.environ.get('GADGETRON_EXTERNAL_LOG_LEVEL', 'DEBUG')),
                        datefmt="%m-%d %H:%M:%S")

    logging.debug(f"Starting external Python module '{args.get('module')}' in state: [ACTIVE]")
    logging.debug(f"Connecting to parent on port {args.get('port')}")

    address = ('localhost', int(args.get('port')))

    with connection.Connection(socket.create_connection(address, 30)) as conn:
        target = load_target(args)
        target(conn)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception as e:
        logging.fatal(e)
        raise e
