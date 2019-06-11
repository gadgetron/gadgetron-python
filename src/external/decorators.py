
from . import connection


def reader(*, slot):
    return lambda r: connection.register_reader(slot=slot, reader=r)


def writer(*, predicate):
    return lambda w: connection.register_writer(predicate=predicate, writer=w)


def module(func):
    pass
