
from . import connection
from . import handlers


def reader(*, slot):

    def register_reader(r):
        connection.register_reader(slot=slot, reader=r)
        return r

    return register_reader


def writer(*, predicate):

    def register_writer(w):
        connection.register_writer(predicate=predicate, writer=w)
        return w

    return register_writer


def module(func):
    handlers.register_handler(func)
    return func
