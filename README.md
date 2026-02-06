# PyClassParser

`PyClassParser` is a Python library designed to parse Python class definitions and extract class attributes. It uses the `attrs` library for defining class attributes and ensures type safety with `attrs-strict`.

Currently it only supports Pydantic class format.

## Features

- Parses Python class definitions to extract class names and their attributes.
- Uses `attrs` for attribute definition and `attrs-strict` for type validation.
- Handles optional attributes and attributes with default values.

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
    attr2: str = "default"

class AnotherClass:
    attr3: float

{'MyClass': [ClassATTR(attr_value='attr1', attr_type='int'), ClassATTR(attr_value='attr2', attr_type='str')], 
 'AnotherClass': [ClassATTR(attr_value='attr3', attr_type='float')]}
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss your ideas.

