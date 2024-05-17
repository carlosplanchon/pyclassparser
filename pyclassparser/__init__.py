#!/usr/bin/env python3

import attrs
from attrs_strict import type_validator

from typing import Optional, Any


@attrs.define()
class ClassATTR:
    attr_value: Any = attrs.field(
        validator=type_validator()
    )
    attr_type: Optional[str] = attrs.field(
        validator=type_validator(),
        default=None
    )


@attrs.define()
class ClassParser:
    code: str = attrs.field(
        validator=type_validator()
    )

    i: Optional[int] = attrs.field(
        validator=type_validator(),
        default=None
    )
    actual_line: Optional[str] = attrs.field(
        validator=type_validator(),
        default=None
    )
    output: str = attrs.field(
        validator=type_validator(),
        default=""
    )

    lines: list[str] = attrs.field(
        validator=type_validator(),
        init=False
    )

    class_data_dict: dict[str, list[ClassATTR]] = attrs.field(
        validator=type_validator(),
        init=False
    )

    def __attrs_post_init__(self):
        self.start()

    def advance(self) -> None:
        if self.i is None:
            self.i = 0
        else:
            self.i += 1

        if self.i < len(self.lines):
            self.actual_line = self.lines[self.i]
        else:
            raise StopIteration

        return None

    def get_class_name(self) -> str:
        class_name: str =\
            self.actual_line.split("class")[1].split("(")[0].strip(": ")
        return class_name

    def get_indentation_spaces_amt(self) -> int:
        indentation_spaces_amt: int = len(
            self.actual_line) - len(self.actual_line.lstrip(" "))
        return indentation_spaces_amt

    def add_attr(self, class_name: str):
        parts: list[str] = self.actual_line.split(":")

        if len(parts) == 2:
            attr_value: str = parts[0]
            attr_type: str = parts[1]
            attr_type: str = attr_type.split("=")[0]

        if len(parts) == 1:
            attr_value: str = parts[0]
            attr_type = None

        attr_value: str = attr_value.strip(" ")

        if attr_type is not None:
            attr_type: str = attr_type.strip(" ")

        class_attr = ClassATTR(
            attr_value=attr_value,
            attr_type=attr_type
        )
        self.class_data_dict[class_name].append(class_attr)

    def get_class_attributes(self, class_name: str):
        self.advance()
        first_attr_indentation: int = self.get_indentation_spaces_amt()
        attrs_indentation: int = first_attr_indentation
        # print(f"> ATTRS Indentation: {attrs_indentation}")
        while attrs_indentation == first_attr_indentation:
            # print(self.actual_line)
            self.output += self.actual_line + "\n"

            self.add_attr(class_name=class_name)

            self.advance()

            attrs_indentation: int = self.get_indentation_spaces_amt()

    def actual_line_is_class(self) -> bool:
        return self.actual_line.lstrip(" ").startswith("class ")

    def get_next_class(self):
        if self.actual_line is None:
            self.advance()

        while self.actual_line_is_class() is False:
            self.advance()

        if self.actual_line_is_class() is True:
            class_name: str = self.get_class_name()
            # print(self.actual_line)
            self.output += "\n\n" + self.actual_line + "\n"

            # Add class data.
            if class_name in self.class_data_dict:
                raise Exception(f"Class name {class_name} already exists.")

            self.class_data_dict[class_name] = []

            self.get_class_attributes(class_name=class_name)

    def start(self):
        self.lines = self.code.split("\n")
        self.class_data_dict: list[list[ClassATTR]] = {}

        while True:
            try:
                self.get_next_class()
            except StopIteration:
                break

        self.output = self.output.strip("\n") + "\n"
