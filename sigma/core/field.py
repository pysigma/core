from collections import OrderedDict
from functools import partial
from types import FunctionType

from .validator import FieldValidator


class option(object):
    """
    Attrs:
      name: The option name (Default is "").
      func: The validation function.
      kwargs: The keyword arguments of the constructor.
      required: Whether this option is required (Default is False).
      value: The option's setting value (Default is None).
      default(option):
        The option's default setting value.
        This attribute is created when "default" keyword argument
        is passed to the constructor.
    """
    def __init__(self, **kwargs):
        """
        Args:
          **kwargs:
            required: Whether this option is required (Default is False).
            default: The option's default setting value.
        """
        self.name = ""
        self.kwargs = kwargs
        self.required = kwargs.get("required", False)
        self.value = None
        if "default" in kwargs:
            self.default = kwargs["default"]

    def __call__(self, name, func):
        """
        Args:
          name: The option name.
          func: The validation function.
        Returns:
          self
        """
        self.name = name
        self.func = func
        return self


class FieldMeta(type):
    """ The Meta Class of Field Class.
    Attrs:
    """
    @classmethod
    def __prepare__(cls, name, bases, **kwds):
        return OrderedDict()

    def __new__(cls, classname, bases, namespace, **kwargs):
        options = {}
        for key, func in namespace.items():
            if key.startswith("_"):
                continue
            if isinstance(func, option):
                options[key] = func
            if isinstance(func, FunctionType):
                options[key] = option()(key, func)
        namespace["__options__"] = options
        namespace.setdefault("__order__", list(options.keys()))
        return type.__new__(cls, classname, bases, namespace, **kwargs)


class Field(object, metaclass=FieldMeta):
    """
    Attrs:
      __order__:
        The list of option names.
        Validation functions is executed in order of this list.
      __options__: The list of option instances.
      __Validator__:
        A FieldValidator class.
      __validator__:
        A __Validator__ instance.
      __model_name__: A Model name.
    """
    __Validator__ = FieldValidator

    def __init__(self, *args, **kwargs):
        """
        Args:
          *args:
            args[0]: A field name.
          *kwargs:
            key: An option name.
            value: An option's setting value.
        """
        self._name = args[0] if args else ""
        self.__kwargs__ = kwargs
        self._value = None
        self.__model_name__ = ""
        validates = []
        for key in self.__order__:
            option = self.__options__[key]
            if key in kwargs:
                option.value = kwargs[key]
                validates.append(
                    partial(option.func, self, option)
                )
            elif hasattr(option, "default"):
                option.value = option.default
                validates.append(
                    partial(option.func, self, option)
                )
            elif option.required:
                validates.append(partial(option.func, self, option))
        self.__validator__ = self.__Validator__()
        self.__validator__.validates = validates

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = self.__validator__.validate(val)

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        self.value = value
