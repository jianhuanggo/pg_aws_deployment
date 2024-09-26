__version__ = "0.5"


class PGObjectSingleton:
    object_registration = {}

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PGObjectSingleton, cls).__new__(cls)
        return cls.instance


class PGObjectMeta(type):
    def __new__(cls, class_name, bases, attrs):
        _object_register = PGObjectSingleton()
        _new_attrs, _object_name, _orig_object_name = {}, None, None
        for _attr_name, _attr_value in attrs.items():
            _new_attrs[_attr_name] = _attr_value
            if _attr_name == "__qualname__" and _attr_value.startswith("PGObject"):
                _object_name = _attr_value[len("PGObject"):]
                _orig_object_name = _attr_value

        _object = type(class_name, bases, _new_attrs)

        if _object_name:
            _object_register.object_registration[_object_name] = {"object_name": _orig_object_name,
                                                                  "object_ptr": _object}
        return _object
