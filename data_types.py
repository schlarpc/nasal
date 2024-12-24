import functools
import re
import abc
import copy
import operator

class callablestaticmethod(staticmethod):
    def __call__(self, cls, *args, **kwargs):
        return self.__get__(None, cls)(*args, **kwargs)

class CoersionError(ValueError):
    pass

class Type(abc.ABC):
    def __init__(self, value=None):
        self._value = self._convert(value)

    @abc.abstractmethod
    def __bool__(self):
        return NotImplemented

    def __add__(self, other):
        return NotImplemented

    def _convert(self, value):
        if isinstance(value, type(self)):
            return copy.copy(value._value)
        raise CoersionError('Unknown data type')

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._value == other._value
        super().__eq__(other)

    def __repr__(self):
        return '<{name} {value!r}>'.format(name=type(self).__qualname__, value=getattr(self, '_value', ''))

    def _coerce_other(self, other):
        return type(self)(other)

    def _generic_operation_value(self, other, operator):
        try:
            return operator(self._value, self._coerce_other(other)._value)
        except CoersionError:
            return NotImplemented

    def _generic_operation_as_type(self, other, operator, return_type):
        try:
            return return_type(self._generic_operation_value(other, operator))
        except CoersionError:
            return NotImplemented

    def _generic_operation(self, other, operator):
        try:
            return self._generic_operation_as_type(other, operator, type(self))
        except CoersionError:
            return NotImplemented

    def __add__(self, other):
        return self._generic_operation(other, operator.add)

    def __radd__(self, other):
        return type(self)(other)._generic_operation(self, operator.add)

    def __sub__(self, other):
        return self._generic_operation(other, operator.sub)

    def __mul__(self, other):
        return self._generic_operation(other, operator.mul)

class Null(Type):
    def __init__(self, value=None):
        super().__init__(value)

    def _convert(self, value):
        if value is None:
            return None
        super()._convert(value)

    def __bool__(self):
        return False

    def __eq__(self, other):
        print('eq')
        if isinstance(other, type(self)):
            return True
        super().__eq__(other)

    def __getitem__(self, key):
        self.__dict__ = Array().__dict__
        self.__class__ = Array
        return Null()

    def _generic_operation(self, other, operator):
        try:
            if isinstance(other, type(self)):
                return type(self)()
            return type(other)(self)._generic_operation(other, operator)
        except CoersionError:
            return NotImplemented

    def __repr__(self):
        return '<{cls}>'.format(cls=type(self).__qualname__)

    def __str__(self):
        return ''

    def as_nasl(self):
        return 'NULL'

    def __typeof__(self):
        return 'undef'

class Integer(Type):
    def __bool__(self):
        return bool(self._value)

    def _convert(self, value):
        if isinstance(value, int):
            return int(value)
        elif isinstance(value, (str, PureString)):
            if re.match(r'^-?(0|[1-9][0-9]*)$', str(value)):
                return int(str(value), 10)
            elif re.match(r'^-?0x[a-fA-F0-9]+$', str(value)):
                return int(str(value), 16)
            elif re.match(r'^-?0[0-7]+$', str(value)):
                return int(str(value), 8)
        elif isinstance(value, bytes):
            return self._convert(value.decode('ascii'))
        elif value is None or isinstance(value, Null):
            return 0
        return super()._convert(value)

    def __int__(self):
        return int(self._value)

    def __str__(self):
        return str(int(self))


    def __truediv__(self, other):
        try:
             return self._generic_operation(other, operator.floordiv)
        except ZeroDivisionError:
            return type(self)(0)

    def __mod__(self, other):
        try:
            return self._generic_operation(other, operator.mod)
        except ZeroDivisionError:
            return type(self)(0)

    def __pow__(self, other):
        return self._generic_operation(other, operator.pow)

    def pre_increment(self):
        self._value += 1
        return self

    def post_increment(self):
        copy = type(self)(self)
        self._value += 1
        return copy

    def pre_decrement(self):
        self._value -= 1
        return self

    def post_decrement(self):
        copy = type(self)(self)
        self._value -= 1
        return copy

    def as_nasl(self):
        return str(self._value)

    def __typeof__(self):
        return 'int'


class PureString(Type):
    def _convert(self, value):
        if isinstance(value, ImpureString):
            raise ValueError()
        elif isinstance(value, str):
            return value.encode('ascii')
        elif isinstance(value, bytes):
            return value.decode('ascii').encode('ascii')
        elif isinstance(value, (int, Integer)):
            return str(value).encode('ascii')
        elif isinstance(value, Null) or value is None:
            return b''
        return super()._convert(value)

    def __bool__(self):
        return bool(self._value and self._value != b"0")

    def __add__(self, other):
        return self._generic_operation(other, operator.add)

    def __sub__(self, other):
        def _sub(obj1, obj2):
            try:
                idx = obj1.index(obj2)
                return obj1[:idx] + obj1[idx+len(obj2):]
            except ValueError:
                return obj1
        return self._generic_operation(other, _sub)

    def __contains__(self, other):
        return self._generic_operation_as_type(other, operator.contains, bool)

    def __getitem__(self, index):
        return type(self)(bytes([self._value[index]]))

    def regex_match(self, pattern):
        raise NotImplementedError()

    def as_nasl(self):
        return "'{}'".format(self._value.decode('ascii'))

    def __str__(self):
        return getattr(self, '_value', b'').decode('ascii')

    def __typeof__(self):
        return 'data'

class ImpureString(PureString):
    pass

class Array(Type):
    def _convert(self, value):
        if value is None:
            return {}
        elif isinstance(value, dict):
            d = {}
            for k, v in value.items():
                if isinstance(k, int):
                    k = Integer(k)
                elif isinstance(k, str):
                    k = String(k)
                elif not isinstance(k, (Integer, String)):
                    raise ValueError()



        return super()._convert(value)

    def as_nasl(self):
        return "[ 1, 2, 'angbak' => 33 ]"

    def __str__(self):
        sorted(self._value.keys()

    def __bool__(self):
        return True

    def __typeof__(self):
        return ''
