"""Parser for Blink schema files."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from ..runtime.errors import SchemaError
from .ast import (
    AnnotationAst,
    BinaryTypeRef,
    EnumDefAst,
    EnumSymbolAst,
    FieldAst,
    GroupDefAst,
    IncrementalAnnotationAst,
    NamedTypeRef,
    ObjectTypeRef,
    PrimitiveTypeRef,
    QName,
    SchemaAst,
    SequenceTypeRef,
    ComponentRefAst,
    TypeDefAst,
    TypeRefAst,
)

KEYWORDS = {
    "i8",
    "u8",
    "i16",
    "u16",
    "i32",
    "u32",
    "i64",
    "u64",
    "f64",
    "decimal",
    "date",
    "timeOfDayMilli",
    "timeOfDayNano",
    "nanotime",
    "millitime",
    "bool",
    "string",
    "binary",
    "fixed",
    "object",
    "namespace",
    "type",
    "schema",
}

BINARY_KINDS = {"string", "binary"}
NUMERIC_ANNOTATION_NAME = QName("blink", "id")


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


class Tokenizer:
    """Converts schema text into a token stream."""

    def __init__(self, text: str) -> None:
        self._text = text
        self._index = 0
        self._line = 1
        self._column = 1
        self.tokens: List[Token] = []
        self._tokenize()

    def _tokenize(self) -> None:
        text = self._text
        while self._index < len(text):
            ch = text[self._index]
            if ch in " \t\r":
                self._advance()
                continue
            if ch == "\n":
                self._advance_line()
                continue
            if ch == "#":
                self._skip_comment()
                continue
            if ch == "-" and self._peek(1) == ">":
                self._emit("ARROW", "->", 2)
                continue
            if ch == "<" and self._peek(1) == "-":
                self._emit("LARROW", "<-", 2)
                continue
            if ch == ":":
                prev = self._text[self._index - 1] if self._index > 0 else ""
                kind = "NS_COLON" if prev and not prev.isspace() else "COLON"
                self._emit(kind, ch, 1)
                continue
            if ch in {".", ",", "/", "*", "[", "]", "(", ")", "?", "|", "@", "="}:
                kind = {
                    ".": "DOT",
                    ",": "COMMA",
                    "/": "SLASH",
                    "*": "STAR",
                    "[": "LBRACKET",
                    "]": "RBRACKET",
                    "(": "LPAREN",
                    ")": "RPAREN",
                    "?": "QUESTION",
                    "|": "PIPE",
                    "@": "AT",
                    "=": "EQUAL",
                }[ch]
                self._emit(kind, ch, 1)
                continue
            if ch == '"' or ch == "'":
                self.tokens.append(self._read_string())
                continue
            if ch in "+-" or ch.isdigit():
                self.tokens.append(self._read_number())
                continue
            if ch == "\\":
                token = self._read_identifier(quoted=True)
                self.tokens.append(token)
                continue
            if ch.isalpha() or ch == "_":
                self.tokens.append(self._read_identifier())
                continue
            raise SchemaError(f"Unexpected character {ch!r} at line {self._line} col {self._column}")
        self.tokens.append(Token("EOF", "", self._line, self._column))

    def _advance(self) -> None:
        self._index += 1
        self._column += 1

    def _advance_line(self) -> None:
        self._index += 1
        self._line += 1
        self._column = 1

    def _peek(self, offset: int) -> str:
        idx = self._index + offset
        if idx >= len(self._text):
            return ""
        return self._text[idx]

    def _emit(self, kind: str, value: str, width: int) -> None:
        token = Token(kind, value, self._line, self._column)
        self.tokens.append(token)
        self._index += width
        self._column += width

    def _skip_comment(self) -> None:
        while self._index < len(self._text) and self._text[self._index] != "\n":
            self._index += 1
        if self._index < len(self._text):
            self._advance_line()

    def _read_string(self) -> Token:
        quote = self._text[self._index]
        line, column = self._line, self._column
        self._index += 1
        self._column += 1
        result = []
        while self._index < len(self._text):
            ch = self._text[self._index]
            if ch == quote:
                self._index += 1
                self._column += 1
                return Token("STRING", "".join(result), line, column)
            if ch == "\\":
                if self._index + 1 >= len(self._text):
                    raise SchemaError(f"Unterminated escape at line {line}")
                result.append(self._decode_escape())
                continue
            if ch == "\n":
                raise SchemaError(f"Unterminated string literal at line {line}")
            result.append(ch)
            self._index += 1
            self._column += 1
        raise SchemaError(f"Unterminated string literal at line {line}")

    def _decode_escape(self) -> str:
        esc = self._text[self._index + 1]
        self._index += 2
        self._column += 2
        if esc == "n":
            return "\n"
        if esc == "t":
            return "\t"
        if esc == "r":
            return "\r"
        if esc in {'"', "'", "\\", "|"}:
            return esc
        if esc == "x":
            digits = self._text[self._index : self._index + 2]
            if len(digits) < 2:
                raise SchemaError("Incomplete hex escape")
            self._index += 2
            self._column += 2
            return chr(int(digits, 16))
        if esc == "u":
            digits = self._text[self._index : self._index + 4]
            if len(digits) < 4:
                raise SchemaError("Incomplete unicode escape")
            self._index += 4
            self._column += 4
            return chr(int(digits, 16))
        if esc == "U":
            digits = self._text[self._index : self._index + 8]
            if len(digits) < 8:
                raise SchemaError("Incomplete unicode escape")
            self._index += 8
            self._column += 8
            return chr(int(digits, 16))
        raise SchemaError(f"Unsupported escape sequence '\\{esc}'")

    def _read_number(self) -> Token:
        line, column = self._line, self._column
        start = self._index
        if self._text[self._index] in "+-":
            self._index += 1
        if self._index >= len(self._text):
            raise SchemaError("Incomplete numeric literal")
        if self._text[self._index : self._index + 2].lower() == "0x":
            self._index += 2
            digits_start = self._index
            while self._index < len(self._text) and self._text[self._index] in "0123456789abcdefABCDEF":
                self._index += 1
            if self._index == digits_start:
                raise SchemaError("Hex literal must include digits")
        else:
            digits_start = self._index
            while self._index < len(self._text) and self._text[self._index].isdigit():
                self._index += 1
            if self._index == digits_start:
                raise SchemaError("Invalid integer literal")
        literal = self._text[start : self._index]
        try:
            value = int(literal, 0)
        except ValueError as exc:
            raise SchemaError(f"Invalid integer literal {literal!r}") from exc
        self._column += self._index - start
        return Token("NUMBER", str(value), line, column)

    def _read_identifier(self, *, quoted: bool = False) -> Token:
        line, column = self._line, self._column
        if quoted:
            self._index += 1
            self._column += 1
            if self._index >= len(self._text):
                raise SchemaError("Dangling escape at end of input")
        start = self._index
        if not (self._text[self._index].isalpha() or self._text[self._index] == "_"):
            raise SchemaError(f"Invalid identifier start {self._text[self._index]!r}")
        self._index += 1
        while self._index < len(self._text):
            ch = self._text[self._index]
            if ch.isalnum() or ch == "_":
                self._index += 1
            else:
                break
        literal = self._text[start : self._index]
        self._column += self._index - start
        if quoted or literal not in KEYWORDS:
            kind = "IDENT"
        else:
            kind = "KEYWORD"
        return Token(kind, literal, line, column)


class Parser:
    """Recursive descent parser for the schema grammar subset."""

    def __init__(self, tokens: Sequence[Token], *, filename: str | None = None) -> None:
        self._tokens = tokens
        self._index = 0
        self._filename = filename or "<schema>"
        self._namespace: str | None = None
        self._enums: List[EnumDefAst] = []
        self._type_defs: List[TypeDefAst] = []
        self._groups: List[GroupDefAst] = []
        self._schema_annotations: List[AnnotationAst] = []
        self._incremental_annotations: List[IncrementalAnnotationAst] = []

    def parse(self) -> SchemaAst:
        while not self._match("EOF"):
            definition_annots = self._parse_annotations()
            token = self._peek()
            if token.kind == "KEYWORD" and token.value == "schema":
                if definition_annots:
                    raise SchemaError("Annotations cannot precede schema annotations")
                self._advance()
                if not self._match("LARROW"):
                    raise SchemaError("schema annotations require '<-'")
                self._schema_annotations.extend(self._parse_incremental_chain())
                continue
            if token.kind == "KEYWORD" and token.value == "namespace":
                if definition_annots:
                    raise SchemaError("Annotations are not allowed on namespace declarations")
                self._advance()
                self._parse_namespace_decl()
                continue
            name, type_id = self._parse_name_with_id()
            member: str | None = None
            if self._match("DOT"):
                member = self._expect_identifier().value
            if self._match("LARROW"):
                if type_id is not None:
                    raise SchemaError("Component references cannot include identifiers")
                annotations = self._parse_incremental_chain()
                self._incremental_annotations.append(
                    IncrementalAnnotationAst(
                        target=ComponentRefAst(name=name, member=member),
                        annotations=tuple(annotations),
                    )
                )
                continue
            if member is not None:
                raise SchemaError("Component references must be followed by '<-'")
            if self._match("EQUAL"):
                saved_index = self._index
                self._parse_annotations()
                is_enum = self._detect_enum()
                self._index = saved_index
                if is_enum:
                    enum_symbols = self._parse_enum_symbols()
                    self._enums.append(
                        EnumDefAst(
                            name=name,
                            symbols=tuple(enum_symbols),
                            annotations=tuple(definition_annots),
                        )
                    )
                else:
                    type_annots = self._parse_annotations()
                    type_ref = self._parse_type()
                    self._type_defs.append(
                        TypeDefAst(
                            name=name,
                            type_ref=type_ref,
                            annotations=tuple(definition_annots + type_annots),
                        )
                    )
            else:
                super_name = None
                if self._match("COLON"):
                    super_name = self._parse_qname()
                fields: Sequence[FieldAst] = tuple()
                if self._match("ARROW"):
                    fields = self._parse_fields()
                group = GroupDefAst(
                    name=name,
                    type_id=type_id,
                    fields=tuple(fields),
                    super_name=super_name,
                    annotations=tuple(definition_annots),
                )
                self._groups.append(group)
        return SchemaAst(
            namespace=self._namespace,
            enums=tuple(self._enums),
            type_defs=tuple(self._type_defs),
            groups=tuple(self._groups),
            schema_annotations=tuple(self._schema_annotations),
            incremental_annotations=tuple(self._incremental_annotations),
        )

    def _parse_namespace_decl(self) -> None:
        if self._namespace is not None:
            raise SchemaError("Duplicate namespace declaration")
        name = self._expect_identifier()
        self._namespace = name.value

    def _parse_fields(self) -> Sequence[FieldAst]:
        fields: List[FieldAst] = []
        while True:
            annotations = self._parse_annotations()
            type_ref = self._parse_type()
            annotations += self._parse_annotations()
            field_name, field_id = self._parse_name_with_id()
            optional = self._match("QUESTION")
            if field_id is not None:
                annotations = list(annotations)
                annotations.append(self._make_numeric_annotation(field_id))
            fields.append(
                FieldAst(
                    name=field_name.name,
                    type_ref=type_ref,
                    optional=optional,
                    annotations=tuple(annotations),
                )
            )
            if not self._match("COMMA"):
                break
        return tuple(fields)

    def _parse_type(self) -> TypeRefAst:
        base = self._parse_single()
        while self._match("LBRACKET"):
            self._expect("RBRACKET")
            base = SequenceTypeRef(base)
        return base

    def _parse_single(self) -> TypeRefAst:
        token = self._peek()
        if token.kind == "KEYWORD":
            if token.value in {
                "i8",
                "u8",
                "i16",
                "u16",
                "i32",
                "u32",
                "i64",
                "u64",
                "f64",
                "decimal",
                "bool",
                "date",
                "timeOfDayMilli",
                "timeOfDayNano",
                "nanotime",
                "millitime",
            }:
                self._advance()
                return PrimitiveTypeRef(token.value)
            if token.value in BINARY_KINDS:
                self._advance()
                size = self._parse_optional_size()
                return BinaryTypeRef(token.value, size)
            if token.value == "fixed":
                self._advance()
                size = self._parse_required_size()
                return BinaryTypeRef("fixed", size)
            if token.value == "object":
                self._advance()
                return ObjectTypeRef()
        qname = self._parse_qname()
        mode = None
        if self._match("STAR"):
            mode = "dynamic"
        return NamedTypeRef(name=qname, group_mode=mode)

    def _parse_optional_size(self) -> int | None:
        if not self._match("LPAREN"):
            return None
        number = self._expect("NUMBER")
        self._expect("RPAREN")
        return int(number.value)

    def _parse_required_size(self) -> int:
        size = self._parse_optional_size()
        if size is None:
            raise SchemaError("Fixed types must specify a size, e.g. fixed(8)")
        return size

    def _parse_enum_symbols(self) -> List[EnumSymbolAst]:
        symbols: List[EnumSymbolAst] = []
        next_value = 0
        self._match("PIPE")
        while True:
            symbol = self._parse_enum_symbol(next_value)
            symbols.append(symbol)
            next_value = symbol.value + 1
            if not self._match("PIPE"):
                break
        return symbols

    def _parse_enum_symbol(self, default_value: int) -> EnumSymbolAst:
        annotations = self._parse_annotations()
        name = self._expect_identifier()
        symbol_value = default_value
        if self._match("SLASH"):
            number = self._expect("NUMBER")
            symbol_value = int(number.value)
        if annotations:
            inline = list(annotations)
        else:
            inline = []
        return EnumSymbolAst(name=name.value, value=symbol_value, annotations=tuple(inline))

    def _parse_incremental_chain(self) -> List[AnnotationAst]:
        annotations: List[AnnotationAst] = []
        while True:
            if self._peek().kind == "NUMBER":
                number = self._advance()
                annotations.append(self._make_numeric_annotation(int(number.value)))
            else:
                chunk = self._parse_annotations()
                if not chunk:
                    raise SchemaError("Expected annotation after '<-'")
                annotations.extend(chunk)
            if not self._match("LARROW"):
                break
        return annotations

    def _make_numeric_annotation(self, value: int) -> AnnotationAst:
        return AnnotationAst(name=NUMERIC_ANNOTATION_NAME, value=str(value))

    def _parse_annotations(self) -> List[AnnotationAst]:
        items: List[AnnotationAst] = []
        while self._match("AT"):
            name = self._parse_qname()
            self._expect("EQUAL")
            value_parts = []
            while self._peek().kind == "STRING":
                value_parts.append(self._advance().value)
            if not value_parts:
                raise SchemaError("Annotation must have a string literal value")
            items.append(AnnotationAst(name=name, value="".join(value_parts)))
        return items

    def _parse_qname(self) -> QName:
        name_token = self._expect_identifier()
        namespace = None
        name = name_token.value
        if self._match("NS_COLON"):
            namespace = name
            name = self._expect_identifier().value
        return QName(namespace, name)

    def _parse_name_with_id(self) -> tuple[QName, int | None]:
        qname = self._parse_qname()
        type_id = None
        if self._match("SLASH"):
            value = self._expect("NUMBER")
            type_id = int(value.value)
        return qname, type_id

    def _detect_enum(self) -> bool:
        token = self._peek()
        if token.kind == "PIPE":
            return True
        if token.kind == "IDENT":
            next_token = self._tokens[self._index + 1] if self._index + 1 < len(self._tokens) else Token("EOF", "", token.line, token.column)
            return next_token.kind in {"PIPE", "SLASH"}
        return False

    def _match(self, kind: str) -> bool:
        if self._peek().kind == kind:
            self._advance()
            return True
        return False

    def _expect(self, kind: str) -> Token:
        token = self._peek()
        if token.kind != kind:
            raise SchemaError(f"Expected {kind}, got {token.kind} at line {token.line}")
        self._advance()
        return token

    def _expect_identifier(self) -> Token:
        token = self._peek()
        if token.kind not in {"IDENT"}:
            raise SchemaError(
                f"Expected identifier at line {token.line}, found {token.kind}"
            )
        self._advance()
        return token

    def _advance(self) -> Token:
        token = self._tokens[self._index]
        self._index += 1
        return token

    def _peek(self) -> Token:
        return self._tokens[self._index]


def parse_schema(text: str, *, filename: str | None = None) -> SchemaAst:
    """Parse Blink schema text into a ``SchemaAst``."""

    tokenizer = Tokenizer(text)
    parser = Parser(tokenizer.tokens, filename=filename)
    return parser.parse()


__all__ = ["parse_schema"]
