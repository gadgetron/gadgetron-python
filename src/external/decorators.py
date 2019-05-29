
import functools


def reader(*, slot):
    print("Hello, I'm the reader decorator!")
    return lambda x: x


def writer(func):
    return func


def module(func):
    pass
