"""Parse Python class definitions and extract their attributes.

The parsing is backed by the standard-library :mod:`ast` module, so it is
robust against blank lines, comments, docstrings, methods, nested classes and
default values that contain colons, none of which need any special handling.

Two results are exposed after construction:

* :attr:`ClassParser.class_data_dict`: maps every top-level class name to the
  list of its attributes (:class:`ClassATTR`).
* :attr:`ClassParser.parsed_code`: a clean, always-valid reconstruction of the
  top-level imports and class stubs (also available as ``.output``).
"""

import ast

import attrs
from attrs_strict import type_validator

from typing import Optional

__all__ = ["ClassATTR", "ClassParser"]


@attrs.define()
class ClassATTR:
    attr_value: str = attrs.field(
        validator=type_validator()
    )
    attr_type: Optional[str] = attrs.field(
        validator=type_validator(),
        default=None
    )
    default_value: Optional[str] = attrs.field(
        validator=type_validator(),
        default=None
    )


@attrs.define()
class ClassParser:
    code: str = attrs.field(
        validator=type_validator()
    )

    parsed_code: str = attrs.field(
        validator=type_validator(),
        init=False,
        default=""
    )
    class_data_dict: dict[str, list[ClassATTR]] = attrs.field(
        validator=type_validator(),
        init=False,
        factory=dict
    )

    def __attrs_post_init__(self) -> None:
        self._parse()

    @property
    def output(self) -> str:
        """Alias for :attr:`parsed_code` (kept for backwards compatibility)."""
        return self.parsed_code

    @staticmethod
    def _assign_target_names(stmt: ast.Assign) -> list[str]:
        """Return the plain ``Name`` targets of an unannotated assignment."""
        names: list[str] = []
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
            elif isinstance(target, (ast.Tuple, ast.List)):
                names.extend(
                    elt.id for elt in target.elts if isinstance(elt, ast.Name)
                )
        return names

    def _extract_attributes(
        self, node: ast.ClassDef
    ) -> tuple[list[ast.stmt], list[ClassATTR]]:
        """Collect the attribute statements of a class body.

        Annotated assignments (``attr: type``) and plain assignments
        (``attr = value``) are treated as attributes. Docstrings, comments,
        methods and nested classes are ignored.
        """
        attr_nodes: list[ast.stmt] = []
        attr_list: list[ClassATTR] = []

        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Name):
                    attr_list.append(
                        ClassATTR(
                            attr_value=stmt.target.id,
                            attr_type=ast.unparse(stmt.annotation),
                            default_value=(
                                ast.unparse(stmt.value)
                                if stmt.value is not None
                                else None
                            )
                        )
                    )
                    attr_nodes.append(stmt)
            elif isinstance(stmt, ast.Assign):
                names: list[str] = self._assign_target_names(stmt)
                if names:
                    default_src: str = ast.unparse(stmt.value)
                    for name in names:
                        attr_list.append(
                            ClassATTR(
                                attr_value=name,
                                attr_type=None,
                                default_value=default_src
                            )
                        )
                    attr_nodes.append(stmt)

        return attr_nodes, attr_list

    def _parse(self) -> None:
        tree: ast.Module = ast.parse(self.code)

        class_data: dict[str, list[ClassATTR]] = {}
        sections: list[str] = []
        import_buffer: list[str] = []

        def flush_imports() -> None:
            if import_buffer:
                sections.append("\n".join(import_buffer))
                import_buffer.clear()

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_buffer.append(ast.unparse(node))
            elif isinstance(node, ast.ClassDef):
                if node.name in class_data:
                    raise ValueError(
                        f"Class name {node.name} already exists."
                    )

                attr_nodes, attr_list = self._extract_attributes(node)
                class_data[node.name] = attr_list

                flush_imports()

                # Re-emit the class from the AST with its body reduced to the
                # attribute statements (or ``pass`` when there are none).
                # Letting ``ast.unparse`` render the whole node keeps
                # decorators, PEP 695 type parameters, bases and keywords
                # intact and correctly indented, including multi-line values.
                new_body: list[ast.stmt] = (
                    attr_nodes if attr_nodes else [ast.Pass()]
                )
                node.body = new_body
                sections.append(ast.unparse(node))

        flush_imports()

        self.class_data_dict = class_data
        # A single trailing newline for real content; empty input stays empty.
        reconstruction: str = "\n\n".join(sections).strip("\n")
        self.parsed_code = f"{reconstruction}\n" if reconstruction else ""
