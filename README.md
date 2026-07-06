**Project:**
[![License](https://img.shields.io/github/license/davidbrownell/dbrownell_ParserLib?color=dark-green)](https://github.com/davidbrownell/dbrownell_ParserLib/blob/master/LICENSE)

**Package:**
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dbrownell_ParserLib?color=dark-green)](https://pypi.org/project/dbrownell_ParserLib/)
[![PyPI - Version](https://img.shields.io/pypi/v/dbrownell_ParserLib?color=dark-green)](https://pypi.org/project/dbrownell_ParserLib/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dbrownell_ParserLib)](https://pypistats.org/packages/dbrownell-parserlib)

**Development:**
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)
[![pytest](https://img.shields.io/badge/pytest-enabled-brightgreen)](https://docs.pytest.org/)
[![CI](https://github.com/davidbrownell/dbrownell_ParserLib/actions/workflows/CICD.yml/badge.svg)](https://github.com/davidbrownell/dbrownell_ParserLib/actions/workflows/CICD.yml)
[![Code Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/davidbrownell/f15146b1b8fdc0a5d45ac0eb786a84f7/raw/dbrownell_ParserLib_code_coverage.json)](https://github.com/davidbrownell/dbrownell_ParserLib/actions)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/davidbrownell/dbrownell_ParserLib?color=dark-green)](https://github.com/davidbrownell/dbrownell_ParserLib/commits/main/)

<!-- Content above this delimiter will be copied to the generated README.md file. DO NOT REMOVE THIS COMMENT, as it will cause regeneration to fail. -->

## Contents
- [Overview](#overview)
- [Installation](#installation)
- [Development](#development)
- [Additional Information](#additional-information)
- [License](#license)

## Overview
`dbrownell_ParserLib` is a Python library that provides utility functionality for creating parsers, with a primary focus on [ANTLR](https://antlr.org) (Another Tool for Language Recognition) integration. The library simplifies the process of building parsers that produce strongly-typed abstract syntax trees (ASTs) with comprehensive source location tracking.

### Key Features
- **ANTLR Integration**: Streamlined wrapper around ANTLR for Python, handling grammar compilation and parser generation
- **AST Representation**: Expression-based AST nodes with automatic parent-child relationship management
- **Source Location Tracking**: Every AST node tracks its source file location (filename, line, column ranges) for detailed error reporting
- **Visitor Pattern**: Flexible visitor pattern implementation with fine-grained traversal control
- **Error Handling**: Rich error objects that associate messages with source locations and extract Python exception tracebacks
- **Multi-threaded Parsing**: Built-in support for parsing multiple files concurrently
- **Workspace Support**: Parse translation units organized across multiple workspace roots
- **Whitespace Handling**: A single visitor mixin supports both insignificant and significant whitespace grammars (e.g., Python-like indentation); grammars that define `INDENT`/`DEDENT` tokens are detected automatically
- **Multiline String Extraction**: Extract multiline string content that must be vertically aligned with its opening token, with detailed errors on misalignment

### How to use `dbrownell_ParserLib`

The typical workflow for creating a parser with this library involves the following steps. For detailed examples, see the test files in the repository, particularly the end-to-end tests that demonstrate complete parsing workflows.


#### 1. Define an ANTLR Grammar
Create a `.g4` grammar file defining your language syntax:

```antlr
grammar Calculator;

expr : expr ('*'|'/') expr   # BinaryOp
     | expr ('+'|'-') expr   # BinaryOp
     | INT                   # Number
     ;

INT : [0-9]+ ;
WS : [ \t\n\r]+ -> skip ;
```

#### 2. Build the Grammar
Use `BuildAntlrGrammar` to generate the lexer and parser:

```python
from pathlib import Path

from dbrownell_ParserLib.antlr.build_antlr_grammar import BuildAntlrGrammar


BuildAntlrGrammar(
    dm,  # DoneManager instance
    Path("Calculator.g4"),
    Path("output_dir"),
)
```

#### 3. Create Custom Visitor
Implement a visitor that converts ANTLR parse trees to Expression objects:

```python
from dataclasses import dataclass

from dbrownell_ParserLib.antlr.antlr_visitor_mixin import AntlrVisitorMixin
from dbrownell_ParserLib.expression import Expression
from dbrownell_ParserLib.terminal_expression import TerminalExpression

from CalculatorVisitor import CalculatorVisitor as GeneratedVisitor


@dataclass(eq=False)
class BinaryExpression(Expression):
    left: Expression
    operator: TerminalExpression[str]
    right: Expression

    def _GenerateAcceptDetails(self):
        yield "left", self.left
        yield "operator", self.operator
        yield "right", self.right


class CalculatorVisitor(AntlrVisitorMixin, GeneratedVisitor):
    def visitBinaryOp(self, ctx):
        operator = TerminalExpression[str](self.CreateRegion(ctx.children[1]), ctx.children[1].getText())

        children = self.GetChildren(ctx)
        assert len(children) == 2, children

        self._stack.append(
            BinaryExpression(
                self.CreateRegion(ctx),
                children[0],
                operator,
                children[1],
            )
        )

    def visitNumber(self, ctx):
        self._stack.append(
            TerminalExpression[int](self.CreateRegion(ctx), int(ctx.getText()))
        )
```

#### 4. Create Parser Instance
Use `CreateAntlrParser` to build a callable parser. Grammars that define `INDENT` and `DEDENT` tokens (significant whitespace) are detected automatically; no additional configuration is required.

```python
from dbrownell_ParserLib.antlr.antlr_parser import CreateAntlrParser


parser = CreateAntlrParser(
    CalculatorLexer,
    CalculatorParser,
    CalculatorVisitor,
    lambda p: p.expr(),  # Entry point rule
)
```

#### 5. Parse Files
Parse single files, multiple files, or entire workspaces:

```python
from dbrownell_ParserLib.errors import Error


# Parse a single file
results = parser(dm, Path("input.txt"), None)

# Parse multiple files
results = parser(dm, [Path("file1.txt"), Path("file2.txt")], None)

# Check results
for filepath, result in results.items():
    if isinstance(result, Error):
        print(f"Parse error in {filepath}: {result}")
    else:
        # result is the visitor containing the parsed AST
        ast = result._stack[0]
        # Process the AST
```

#### 6. Traverse the AST
Use the visitor pattern to process your AST:

```python
from contextlib import contextmanager

from dbrownell_ParserLib.visitors import ExpressionVisitorHelper, VisitResult


class EvaluatorVisitor(ExpressionVisitorHelper):
    @contextmanager
    def OnBinaryExpression(self, expression):
        # Process binary expressions
        yield VisitResult.Continue


ast.Accept(EvaluatorVisitor())
```

<!-- Content below this delimiter will be copied to the generated README.md file. DO NOT REMOVE THIS COMMENT, as it will cause regeneration to fail. -->

## Installation

| Installation Method | Command |
| --- | --- |
| Via [uv](https://github.com/astral-sh/uv) | `uv add dbrownell_ParserLib` |
| Via [pip](https://pip.pypa.io/en/stable/) | `pip install dbrownell_ParserLib` |

### Verifying Signed Artifacts
Artifacts are signed and verified using [py-minisign](https://github.com/x13a/py-minisign) and the public key in the file `./minisign_key.pub`.

To verify that an artifact is valid, visit [the latest release](https://github.com/davidbrownell/dbrownell_ParserLib/releases/latest) and download the `.minisign` signature file that corresponds to the artifact, then run the following command, replacing `<filename>` with the name of the artifact to be verified:

```shell
uv run --with py-minisign python -c "import minisign; minisign.PublicKey.from_file('minisign_key.pub').verify_file('<filename>'); print('The file has been verified.')"
```

## Development
Please visit [Contributing](https://github.com/davidbrownell/dbrownell_ParserLib/blob/main/CONTRIBUTING.md) and [Development](https://github.com/davidbrownell/dbrownell_ParserLib/blob/main/DEVELOPMENT.md) for information on contributing to this project.

## Additional Information
Additional information can be found at these locations.

| Title | Document | Description |
| --- | --- | --- |
| Code of Conduct | [CODE_OF_CONDUCT.md](https://github.com/davidbrownell/dbrownell_ParserLib/blob/main/CODE_OF_CONDUCT.md) | Information about the norms, rules, and responsibilities we adhere to when participating in this open source community. |
| Contributing | [CONTRIBUTING.md](https://github.com/davidbrownell/dbrownell_ParserLib/blob/main/CONTRIBUTING.md) | Information about contributing to this project. |
| Development | [DEVELOPMENT.md](https://github.com/davidbrownell/dbrownell_ParserLib/blob/main/DEVELOPMENT.md) | Information about development activities involved in making changes to this project. |
| Governance | [GOVERNANCE.md](https://github.com/davidbrownell/dbrownell_ParserLib/blob/main/GOVERNANCE.md) | Information about how this project is governed. |
| Maintainers | [MAINTAINERS.md](https://github.com/davidbrownell/dbrownell_ParserLib/blob/main/MAINTAINERS.md) | Information about individuals who maintain this project. |
| Security | [SECURITY.md](https://github.com/davidbrownell/dbrownell_ParserLib/blob/main/SECURITY.md) | Information about how to privately report security issues associated with this project. |

## License
`dbrownell_ParserLib` is licensed under the <a href="https://choosealicense.com/licenses/MIT/" target="_blank">MIT</a> license.
