import struct
from typing import TypeVar, Generic, Protocol, runtime_checkable, Iterable, Tuple, get_args, List, get_origin, Union
from abc import abstractmethod

import inspect
from gadgetron.external import constants

__reader_predicate_list = []
__reader_type_map = {}
__writer_predicate_list = []
__writer_type_map = {}

T = TypeVar('T')

@runtime_checkable
class Vector(Protocol[T]):
    shape: Tuple[int]
    @abstractmethod
    def tobytes(self, order: str):
        raise NotImplementedError()

@runtime_checkable
class NDArray(Protocol[T]):
    flat: Iterable[T]
    shape: tuple

    @abstractmethod
    def tobytes(self, order: str):
        raise NotImplementedError()


def serializer(predicate_list, type_map, num_params, *, data_type=None, predicate=None):
    if predicate and data_type:
        predicate2 = lambda t: predicate(t) and t is data_type
    else:
        predicate2 = predicate

    if not predicate and not data_type:
        raise TypeError("predicate or/and data_type must be supplied")

    def serializer_decorator(func):
        func_params = len(inspect.signature(func).parameters)
        if func_params == num_params - 1:
            serializer_func = lambda *args: func(*args[:-1])
        else:
            serializer_func = func

        if predicate2:
            predicate_list.append((predicate2, serializer_func))
        else:
            type_map[data_type] = serializer_func
        return func

    return serializer_decorator


def message_reader(obj_type):
    return lambda source: read(source, obj_type)


def message_writer(message_id, obj_type):
    def wrapped_writer(source, obj):
        write(source, message_id, constants.GadgetMessageIdentifier)
        write(source, obj, obj_type)

    return wrapped_writer


def reader(data_type=None, *, predicate=None):
    return serializer(__reader_predicate_list, __reader_type_map, num_params=2, data_type=data_type,
                      predicate=predicate)


def writer(data_type=None, *, predicate=None):
    return serializer(__writer_predicate_list, __writer_type_map, num_params=3, data_type=data_type,
                      predicate=predicate)


def istype(obj_type):
    return lambda t: obj_type is t


def isgeneric(obj_type):
    return lambda t: get_origin(t) is obj_type


def isoptional(obj_type):
    args = get_args(obj_type)
    if not get_origin(obj_type) is Union: return False
    if len(args) != 2: return False
    if args[1] is not type(None): return False

    return True


def isstruct(obj_type):
    return type(obj_type) is struct.Struct


def inheritsfrom(base_class):
    return lambda other_type: issubclass(other_type, base_class) if isinstance(other_type,type) else False


def read(source, obj_type):
    if obj_type in __reader_type_map:
        read_func = __reader_type_map[obj_type]
    else:
        read_func = next((func for pred, func in reversed(__reader_predicate_list) if pred(obj_type)), None)
    if not read_func: raise TypeError(f"Type {obj_type} has no registered reader")
    return read_func(source, obj_type)


def write(source, obj, obj_type):
    if obj_type in __writer_type_map:
        writer_func = __writer_type_map[obj_type]
    else:
        writer_func = next((func for pred, func in reversed(__writer_predicate_list) if pred(obj_type)), None)
    if not writer_func: raise TypeError(f"Type {obj_type} has no registered writer")
    return writer_func(source, obj, obj_type)


if __name__ == "__main__":
    print(get_args(NDArray[float]))
    pass
