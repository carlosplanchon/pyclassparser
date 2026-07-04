"""Test suite for :mod:`pyclassparser`.

Besides the happy-path checks, every test whose name starts with
``test_regression_`` pins down a bug that existed in the previous,
string-splitting implementation and is fixed by the AST-based parser.
"""

import ast
import sys
import textwrap

import pytest

from pyclassparser import ClassATTR, ClassParser


def parse(code: str) -> ClassParser:
    """Parse ``code`` after stripping shared leading indentation."""
    return ClassParser(code=textwrap.dedent(code))


# --------------------------------------------------------------------------- #
# Baseline / documented behaviour                                             #
# --------------------------------------------------------------------------- #
def test_readme_baseline_class_data_dict():
    parser = parse(
        """
        class MyClass:
            attr1: int
            attr2: str = "default"

        class AnotherClass:
            attr3: float
        """
    )
    assert parser.class_data_dict == {
        "MyClass": [
            ClassATTR(attr_value="attr1", attr_type="int"),
            ClassATTR(
                attr_value="attr2", attr_type="str", default_value="'default'"
            ),
        ],
        "AnotherClass": [
            ClassATTR(attr_value="attr3", attr_type="float"),
        ],
    }


def test_readme_baseline_parsed_code():
    parser = parse(
        """
        class MyClass:
            attr1: int
            attr2: str = "default"

        class AnotherClass:
            attr3: float
        """
    )
    assert parser.parsed_code == (
        "class MyClass:\n"
        "    attr1: int\n"
        "    attr2: str = 'default'\n"
        "\n"
        "class AnotherClass:\n"
        "    attr3: float\n"
    )


def test_output_property_aliases_parsed_code():
    parser = parse(
        """
        class MyClass:
            attr1: int
        """
    )
    assert parser.output == parser.parsed_code


def test_parsed_code_is_always_valid_python():
    parser = parse(
        """
        from typing import Optional

        class MyClass:
            mapping: dict = {"a": 1}
            started: str = "12:30"

        class Empty:
            \"\"\"Only a docstring.\"\"\"
        """
    )
    # Must not raise: parsed_code is guaranteed to be valid, parseable Python.
    ast.parse(parser.parsed_code)


# --------------------------------------------------------------------------- #
# Regressions: crashes in the old implementation                              #
# --------------------------------------------------------------------------- #
def test_regression_colon_in_dict_default():
    # Old code raised UnboundLocalError (line had two ':').
    parser = parse(
        """
        class MyClass:
            mapping: dict = {"a": 1}
        """
    )
    assert parser.class_data_dict == {
        "MyClass": [
            ClassATTR(
                attr_value="mapping",
                attr_type="dict",
                default_value="{'a': 1}",
            )
        ]
    }


def test_regression_colon_in_string_default():
    # Old code raised UnboundLocalError on the ':' inside "12:30".
    parser = parse(
        """
        class MyClass:
            started: str = "12:30"
        """
    )
    assert parser.class_data_dict == {
        "MyClass": [
            ClassATTR(
                attr_value="started",
                attr_type="str",
                default_value="'12:30'",
            )
        ]
    }


def test_regression_inline_comment_with_colon():
    # Old code raised UnboundLocalError on the ':' inside the comment.
    parser = parse(
        """
        class MyClass:
            attr1: int  # note: important
        """
    )
    assert parser.class_data_dict == {
        "MyClass": [ClassATTR(attr_value="attr1", attr_type="int")]
    }


# --------------------------------------------------------------------------- #
# Regressions: silent data loss / wrong data in the old implementation        #
# --------------------------------------------------------------------------- #
def test_regression_blank_line_between_attributes():
    # Old code dropped every attribute after the first blank line.
    parser = parse(
        """
        class MyClass:
            attr1: int

            attr2: str
        """
    )
    assert parser.class_data_dict == {
        "MyClass": [
            ClassATTR(attr_value="attr1", attr_type="int"),
            ClassATTR(attr_value="attr2", attr_type="str"),
        ]
    }


def test_regression_class_name_containing_substring_class():
    # Old code did .split("class") and mangled 'Subclass' into 'Sub'.
    parser = parse(
        """
        class Subclass:
            attr1: int
        """
    )
    assert list(parser.class_data_dict) == ["Subclass"]


def test_regression_comment_line_is_ignored():
    # Old code captured '# comment' as an attribute.
    parser = parse(
        """
        class MyClass:
            # this is a comment
            attr1: int
        """
    )
    assert parser.class_data_dict == {
        "MyClass": [ClassATTR(attr_value="attr1", attr_type="int")]
    }


def test_regression_docstring_is_ignored():
    # Old code captured the docstring as an attribute.
    parser = parse(
        '''
        class MyClass:
            """Docs."""
            attr1: int
        '''
    )
    assert parser.class_data_dict == {
        "MyClass": [ClassATTR(attr_value="attr1", attr_type="int")]
    }


def test_regression_methods_are_ignored():
    # Old code captured 'def foo(self)' as an attribute.
    parser = parse(
        """
        class MyClass:
            attr1: int

            def foo(self):
                return 1
        """
    )
    assert parser.class_data_dict == {
        "MyClass": [ClassATTR(attr_value="attr1", attr_type="int")]
    }
    assert "def foo" not in parser.parsed_code


def test_nested_classes_are_ignored():
    parser = parse(
        """
        class Outer:
            attr1: int

            class Inner:
                attr2: str
        """
    )
    # Only the top-level class is reported, and Inner is not an attribute.
    assert list(parser.class_data_dict) == ["Outer"]
    assert parser.class_data_dict["Outer"] == [
        ClassATTR(attr_value="attr1", attr_type="int")
    ]


# --------------------------------------------------------------------------- #
# Annotations & assignments                                                   #
# --------------------------------------------------------------------------- #
def test_generic_and_optional_annotations_preserved():
    parser = parse(
        """
        from typing import Optional

        class MyClass:
            a: Optional[int] = None
            b: dict[str, int]
            c: list[str] = []
        """
    )
    assert parser.class_data_dict == {
        "MyClass": [
            ClassATTR(
                attr_value="a", attr_type="Optional[int]", default_value="None"
            ),
            ClassATTR(attr_value="b", attr_type="dict[str, int]"),
            ClassATTR(
                attr_value="c", attr_type="list[str]", default_value="[]"
            ),
        ]
    }


def test_unannotated_assignment_has_none_type():
    parser = parse(
        """
        class MyClass:
            x: int
            model_config = {"frozen": True}
        """
    )
    assert parser.class_data_dict == {
        "MyClass": [
            ClassATTR(attr_value="x", attr_type="int"),
            ClassATTR(
                attr_value="model_config",
                attr_type=None,
                default_value="{'frozen': True}",
            ),
        ]
    }


# --------------------------------------------------------------------------- #
# parsed_code reconstruction                                                  #
# --------------------------------------------------------------------------- #
def test_imports_are_collected_before_the_class():
    parser = parse(
        """
        import os
        from typing import Optional

        class MyClass:
            attr1: int
        """
    )
    assert parser.parsed_code == (
        "import os\n"
        "from typing import Optional\n"
        "\n"
        "class MyClass:\n"
        "    attr1: int\n"
    )


def test_class_bases_and_keywords_preserved_in_header():
    parser = parse(
        """
        class MyModel(BaseModel, metaclass=ABCMeta):
            attr1: int
        """
    )
    assert parser.parsed_code.startswith(
        "class MyModel(BaseModel, metaclass=ABCMeta):"
    )


def test_class_decorators_preserved():
    parser = parse(
        """
        @dataclass
        @final
        class Point:
            x: int
            y: int = 0
        """
    )
    assert parser.class_data_dict == {
        "Point": [
            ClassATTR(attr_value="x", attr_type="int"),
            ClassATTR(attr_value="y", attr_type="int", default_value="0"),
        ]
    }
    assert parser.parsed_code == (
        "@dataclass\n"
        "@final\n"
        "class Point:\n"
        "    x: int\n"
        "    y: int = 0\n"
    )


@pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="PEP 695 type parameter syntax (class Box[T]) only parses on 3.12+",
)
def test_regression_pep695_generic_class_preserved():
    # A manually rebuilt header used to drop the ``[T]`` type parameters.
    parser = parse(
        """
        class Box[T](Base):
            item: T
        """
    )
    assert list(parser.class_data_dict) == ["Box"]
    assert parser.parsed_code.startswith("class Box[T](Base):")


def test_multiline_string_default_stays_valid():
    parser = parse(
        '''
        class Doc:
            body: str = """first
        second
        third"""
        '''
    )
    (attr,) = parser.class_data_dict["Doc"]
    assert attr.attr_value == "body"
    assert attr.attr_type == "str"
    # The multi-line default must not corrupt the indentation of parsed_code.
    ast.parse(parser.parsed_code)


def test_empty_class_body_becomes_pass():
    parser = parse(
        '''
        class Empty:
            """Only a docstring, no attributes."""
        '''
    )
    assert parser.class_data_dict == {"Empty": []}
    assert parser.parsed_code == "class Empty:\n    pass\n"


def test_only_imports_no_class():
    parser = parse(
        """
        import os
        from sys import path
        """
    )
    assert parser.class_data_dict == {}
    assert parser.parsed_code == "import os\nfrom sys import path\n"


# --------------------------------------------------------------------------- #
# Edge cases & error handling                                                 #
# --------------------------------------------------------------------------- #
def test_no_trailing_newline():
    parser = ClassParser(code="class MyClass:\n    attr1: int")
    assert parser.class_data_dict == {
        "MyClass": [ClassATTR(attr_value="attr1", attr_type="int")]
    }


def test_empty_input():
    parser = ClassParser(code="")
    assert parser.class_data_dict == {}
    assert parser.parsed_code == ""


def test_input_without_classes_or_imports_is_empty():
    parser = parse(
        """
        VERSION = "1.0"

        def helper():
            return 1
        """
    )
    assert parser.class_data_dict == {}
    assert parser.parsed_code == ""


def test_duplicate_top_level_class_name_raises():
    with pytest.raises(ValueError, match="already exists"):
        parse(
            """
            class MyClass:
                a: int

            class MyClass:
                b: str
            """
        )


def test_syntax_error_propagates():
    with pytest.raises(SyntaxError):
        ClassParser(code="class :::")


# --------------------------------------------------------------------------- #
# ClassATTR itself                                                            #
# --------------------------------------------------------------------------- #
def test_classattr_equality_and_defaults():
    assert ClassATTR(attr_value="a", attr_type="int") == ClassATTR(
        attr_value="a", attr_type="int"
    )
    assert ClassATTR(attr_value="a").attr_type is None
    assert ClassATTR(attr_value="a").default_value is None


def test_default_value_is_captured():
    parser = parse(
        """
        class C:
            a: int
            b: int = 5
            c: str = "x"
            d = [1, 2]
        """
    )
    assert parser.class_data_dict["C"] == [
        ClassATTR(attr_value="a", attr_type="int", default_value=None),
        ClassATTR(attr_value="b", attr_type="int", default_value="5"),
        ClassATTR(attr_value="c", attr_type="str", default_value="'x'"),
        ClassATTR(attr_value="d", attr_type=None, default_value="[1, 2]"),
    ]


def test_classattr_rejects_non_string_value():
    # The "type safety" promise from the README (attrs-strict validation).
    with pytest.raises(ValueError):
        ClassATTR(attr_value=123)
