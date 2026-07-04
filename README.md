# PyClassParser

[![CI](https://github.com/carlosplanchon/pyclassparser/actions/workflows/ci.yml/badge.svg)](https://github.com/carlosplanchon/pyclassparser/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/pyclassparser.svg)](https://pypi.org/project/pyclassparser/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyclassparser.svg)](https://pypi.org/project/pyclassparser/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/carlosplanchon/pyclassparser)

`PyClassParser` is a Python library designed to parse Python class definitions and extract class attributes. Parsing is backed by the standard-library `ast` module, so it is robust against blank lines, comments, docstrings, methods, nested classes and default values that contain colons. It uses the `attrs` library for defining the result objects and ensures type safety with `attrs-strict`.

## Features

- Parses Python class definitions to extract class names and their attributes.
- Uses the standard-library `ast` module, so the input must be syntactically valid Python (a `SyntaxError` is raised otherwise).
- Uses `attrs` for the result objects and `attrs-strict` for type validation.
- Handles optional attributes and attributes with default values.
- Rebuilds a clean, always-valid reconstruction of the imports and class stubs.

## Installation with UV:

```bash
uv add pyclassparser
```

## Usage

Here's how you can use `PyClassParser` to parse Python class definitions:

### Example Code

Create a Python script, for example `example.py`:

```python
from pyclassparser import ClassParser

code = """
class MyClass:
    attr1: int
    attr2: str = "default"

class AnotherClass:
    attr3: float
"""
parser = ClassParser(code=code)
print(parser.output)
print(parser.class_data_dict)
```

### Example Output

Running the above script should give you the parsed output of class definitions:

```
class MyClass:
    attr1: int
    attr2: str = 'default'

class AnotherClass:
    attr3: float

{'MyClass': [ClassATTR(attr_value='attr1', attr_type='int'), ClassATTR(attr_value='attr2', attr_type='str')], 
 'AnotherClass': [ClassATTR(attr_value='attr3', attr_type='float')]}
```

> Note: `parser.parsed_code` is an alias of `parser.output`. Because the code is
> re-emitted from the AST, string literals are normalized (e.g. `"default"`
> becomes `'default'`).

## What gets parsed

- Only **top-level** classes are reported; nested classes are ignored.
- An attribute is either an annotated assignment (`attr: type`) — whose
  `attr_type` is the annotation — or a plain assignment (`attr = value`), whose
  `attr_type` is `None`.
- Docstrings, comments, methods and nested classes are ignored.
- Class-level decorators and PEP 695 type parameters (`class Box[T]:`) are kept in `parsed_code`.
- A duplicate top-level class name raises `ValueError`.

## Running the tests

```bash
uv sync
uv run pytest
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss your ideas.

