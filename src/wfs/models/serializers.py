class _Absent:
    def __repr__(self):
        return "<absent>"

    def __bool__(self):
        return False


ABSENT = _Absent()


class SerializerError(Exception):
    """Base class for serializer errors."""


class ValidationError(SerializerError):
    """Raised when input fails validation during deserialize()."""


def _get(value, name, default):
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


class BaseSerializer:
    """
    Built-in primitives leave `schema` as None and implement primitive only methods.
    User-defined serializers instead set `schema` to another serializer (typically F.dict(...)) and inherit the behavior.

    Options:
      null        -- allow None as a value.
      default     -- value (or zero-arg callable) used by a parent
                     DictSerializer when this field is absent.
      required    -- whether a parent DictSerializer requires this field on
                     input (default True; ignored when a default is given).
      read_only   -- include on output, ignore on input (DRF: read_only).
      write_only  -- accept on input, omit from output (DRF: write_only).
    """

    schema = None

    def __init__(
        self,
        null=False,
        default=ABSENT,
        required=True,
        read_only=False,
        write_only=False,
    ):
        self.null = null
        self.default = default
        self.required = required
        self.read_only = read_only
        self.write_only = write_only

    def serialize(self, value=ABSENT):
        # class attribute, not instance level
        schema = type(self).schema
        if schema is not None:
            return schema.serialize(value)
        else:
            if value is None:
                if self.null:
                    return None
                raise ValidationError("value may not be null")
            if value is ABSENT:
                if self.has_default():
                    value = self.resolve_default()
                else:
                    if self.required:
                        raise ValidationError("value is required")
            return self._serialize_primitive_only(value)

    def deserialize(self, value=ABSENT):
        schema = type(self).schema
        if schema is not None:
            return schema.deserialize(value)
        else:
            if value is None:
                if self.null:
                    return None
                else:
                    raise ValidationError("value may not be null")
            else:
                is_valid, msg = self._validate(value)
                if is_valid:
                    return self._deserialize_primitive_only(value)
                else:
                    raise ValidationError(msg)

    def has_default(self):
        return self.default is not ABSENT

    def resolve_default(self):
        return self.default() if callable(self.default) else self.default

    def _validate(self, value):
        """Return (is_valid, message). Called before _deserialize_primitive_only."""
        raise NotImplementedError

    def _serialize_primitive_only(self, value):
        raise NotImplementedError

    def _deserialize_primitive_only(self, value):
        """Transform an already-validated value. Assumes _validate() passed."""
        raise NotImplementedError

    def __repr__(self):
        return f"{type(self).__name__}(null={self.null}, required={self.required})"


class StringSerializer(BaseSerializer):
    def _validate(self, value):
        if not isinstance(value, str):
            return False, f"expected a string, got {type(value).__name__}"
        return True, None

    def _serialize_primitive_only(self, value):
        return str(value)

    def _deserialize_primitive_only(self, value):
        return value


class IntegerSerializer(BaseSerializer):
    def _validate(self, value):
        # bool is a subclass of int; reject it explicitly.
        if isinstance(value, bool) or not isinstance(value, int):
            return False, f"expected an integer, got {type(value).__name__}"
        return True, None

    def _serialize_primitive_only(self, value):
        return int(value)

    def _deserialize_primitive_only(self, value):
        return value


class FloatSerializer(BaseSerializer):
    def _validate(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False, f"expected a float, got {type(value).__name__}"
        return True, None

    def _serialize_primitive_only(self, value):
        return float(value)

    def _deserialize_primitive_only(self, value):
        return float(value)


class BooleanSerializer(BaseSerializer):
    TRUE_VALUES = {"true", "t", "yes", "y", "on", "1"}
    FALSE_VALUES = {"false", "f", "no", "n", "off", "0"}

    def _coerce(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            if value == 1:
                return True
            if value == 0:
                return False
        elif isinstance(value, str):
            key = value.strip().lower()
            if key in self.TRUE_VALUES:
                return True
            if key in self.FALSE_VALUES:
                return False
        return None

    def _validate(self, value):
        if self._coerce(value) is None:
            return False, f"expected a boolean, got {value!r}"
        return True, None

    def _serialize_primitive_only(self, value):
        coerced = self._coerce(value)
        return coerced if coerced is not None else bool(value)

    def _deserialize_primitive_only(self, value):
        return self._coerce(value)


class ArraySerializer(BaseSerializer):
    def __init__(self, items=None, **kwargs):
        super().__init__(**kwargs)
        self.items = items

    def _validate(self, value):
        if not isinstance(value, (list, tuple)):
            return False, f"expected an array, got {type(value).__name__}"
        return True, None

    def _serialize_primitive_only(self, value):
        if self.items is None:
            return list(value)
        return [self.items.serialize(v) for v in value]

    def _deserialize_primitive_only(self, value):
        if self.items is None:
            return list(value)
        out = []
        for i, v in enumerate(value):
            try:
                out.append(self.items.deserialize(v))
            except ValidationError as e:
                raise ValidationError(f"[{i}]: {e}") from e
        return out


class DictSerializer(BaseSerializer):
    """An object/struct: a mapping of field name -> serializer.

    Fields are usually given as keyword args, e.g. F.dict(name=F.string()). The
    serializer-level options are keyword-only; to use a field literally named one
    of those, pass fields via the positional mapping: F.dict({"required": ...}).
    """

    def __init__(
        self,
        fields=None,
        *,
        null=False,
        default=ABSENT,
        required=True,
        read_only=False,
        write_only=False,
        **field_kwargs,
    ):
        super().__init__(
            null=null,
            default=default,
            required=required,
            read_only=read_only,
            write_only=write_only,
        )
        self.fields = dict(fields or dict())
        self.fields.update(field_kwargs)

    def _validate(self, value):
        if not isinstance(value, dict):
            return False, f"expected an object, got {type(value).__name__}"
        return True, None

    def _serialize_primitive_only(self, value):
        out = {}
        for name, ser in self.fields.items():
            if ser.write_only:
                continue
            raw = _get(value, name, ABSENT)
            out[name] = ser.serialize(raw)
        return out

    def _deserialize_primitive_only(self, value):
        out = {}
        for name, ser in self.fields.items():
            if ser.read_only:
                continue
            if name in value:
                try:
                    out[name] = ser.deserialize(value[name])
                except ValidationError as e:
                    raise ValidationError(f"{name}: {e}") from e
            elif ser.has_default():
                out[name] = ser.resolve_default()
            elif ser.required:
                raise ValidationError(f"missing required field: {name}")
            else:
                out[name] = None
        return out


class F:
    string = StringSerializer
    integer = IntegerSerializer
    float = FloatSerializer
    boolean = BooleanSerializer
    array = ArraySerializer
    dict = DictSerializer


class ObjectSerializer(BaseSerializer):
    schema = F.dict(
        key=F.string(),
        size=F.integer(),
        etag=F.string(null=True, read_only=True),
        last_modified=F.string(null=True, read_only=True),
    )
