import pytest

from wfs.models.serializers import BaseSerializer, F, ValidationError


def test_string_roundtrip():
    s = F.string()
    assert s.deserialize("hi") == "hi"
    assert s.serialize("hi") == "hi"


def test_string_rejects_non_string():
    with pytest.raises(ValidationError):
        F.string().deserialize(5)


def test_null_allowed_vs_disallowed():
    assert F.string(null=True).deserialize(None) is None
    with pytest.raises(ValidationError):
        F.string().deserialize(None)


def test_integer_rejects_bool():
    with pytest.raises(ValidationError):
        F.integer().deserialize(True)


def test_float_coerces_int():
    assert F.float().deserialize(3) == 3.0


def test_boolean_coercion():
    b = F.boolean()
    assert b.deserialize("true") is True
    assert b.deserialize("No") is False
    assert b.deserialize(1) is True
    assert b.deserialize(0) is False
    assert b.deserialize(True) is True
    with pytest.raises(ValidationError):
        b.deserialize("maybe")


def test_array_of_strings():
    a = F.array(F.string())
    assert a.deserialize(["a", "b"]) == ["a", "b"]
    with pytest.raises(ValidationError) as exc:
        a.deserialize(["a", 1])
    assert "[1]" in str(exc.value)


def test_dict_required_and_optional():
    d = F.dict(name=F.string(), nick=F.string(null=True, required=False))
    assert d.deserialize({"name": "x"}) == {"name": "x", "nick": None}
    with pytest.raises(ValidationError):
        d.deserialize({})


def test_dict_default_callable():
    d = F.dict(tags=F.array(F.string(), default=list))
    assert d.deserialize({}) == {"tags": []}


def test_dict_error_includes_field_name():
    d = F.dict(size=F.integer())
    with pytest.raises(ValidationError) as exc:
        d.deserialize({"size": "x"})
    assert "size" in str(exc.value)


def test_read_only_excluded_from_input():
    d = F.dict(name=F.string(), etag=F.string(read_only=True))
    # read_only field is ignored on input even if present...
    assert d.deserialize({"name": "x", "etag": "abc"}) == {"name": "x"}
    # ...and not required on input.
    assert d.deserialize({"name": "x"}) == {"name": "x"}


def test_write_only_excluded_from_output():
    d = F.dict(name=F.string(), secret=F.string(write_only=True))
    assert d.serialize({"name": "x", "secret": "shh"}) == {"name": "x"}


def test_serialize_reads_object_attributes():
    class Obj:
        key = "a.txt"
        size = 3

    d = F.dict(key=F.string(), size=F.integer())
    assert d.serialize(Obj()) == {"key": "a.txt", "size": 3}


def test_object_serializer_subclass_roundtrip():
    class PointSerializer(BaseSerializer):
        schema = F.dict(x=F.number(), y=F.number())

    data = {"x": 1, "y": 2.5}
    assert PointSerializer().deserialize(data) == data
    assert PointSerializer().serialize(data) == data


def test_nested_dicts():
    d = F.dict(meta=F.dict(etag=F.string(null=True)))
    assert d.deserialize({"meta": {"etag": None}}) == {"meta": {"etag": None}}
