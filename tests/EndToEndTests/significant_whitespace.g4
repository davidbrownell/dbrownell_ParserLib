grammar significant_whitespace;

// ----------------------------------------------------------------------
tokens { INDENT, DEDENT }

@lexer::header {

from antlr_denter.DenterHelper import DenterHelper
from significant_whitespaceParser import significant_whitespaceParser

}

@lexer::members {

def CustomInit(self):
    self._nested_pair_ctr = 0


class significant_whitespaceDenter(DenterHelper):
    def __init__(self, lexer, newline_token, indent_token, dedent_token):
        super().__init__(newline_token, indent_token, dedent_token, should_ignore_eof=False)

        self.lexer: significant_whitespaceLexer = lexer

    def pull_token(self):
        return super(significant_whitespaceLexer, self.lexer).nextToken()

def nextToken(self):
    if not hasattr(self, "_denter"):
        self._denter = self.__class__.significant_whitespaceDenter(
            self,
            significant_whitespaceParser.NEWLINE,
            significant_whitespaceParser.INDENT,
            significant_whitespaceParser.DEDENT,
        )

    return self._denter.next_token()
}

// ----------------------------------------------------------------------
// |
// |  Lexer Rules
// |
// ----------------------------------------------------------------------
HORIZONTAL_WHITESPACE:                      [ \t]+ -> channel(HIDDEN);

// ----------------------------------------------------------------------
// Newlines nested within paired brackets brackets are safe to ignore, but newlines outside of paired
// brackets are meaningful.
NEWLINE:                                    '\r'? '\n' {self._nested_pair_ctr == 0}? [ \t]*;
NESTED_NEWLINE:                             '\r'? '\n' {self._nested_pair_ctr != 0}? [ \t]* -> channel(HIDDEN);

LINE_CONTINUATION:                          '\\' '\r'? '\n' [ \t]* -> channel(HIDDEN);

LPAREN:                                     '(' {self._nested_pair_ctr += 1};
RPAREN:                                     ')' {self._nested_pair_ctr -= 1};
LBRACK:                                     '[' {self._nested_pair_ctr += 1};
RBRACK:                                     ']' {self._nested_pair_ctr -= 1};

INT:                                        [0-9]+;

// ----------------------------------------------------------------------
// |
// |  Parser Rules
// |
// ----------------------------------------------------------------------
// Note that any rule with a '__' suffix represents a non-binding rule (meaning a rule without
// backing code only here for organizational purposes).

// ----------------------------------------------------------------------
entry_point__ : expr__* EOF;
expr__: (atom_expr | unary_expr | power_expr | mul_div_expr | add_sub_expr);
atom_expr: INT NEWLINE;
unary_expr: 'u' ('+' | '-') INDENT expr__ DEDENT;
power_expr: '**' INDENT expr__ expr__ DEDENT;
mul_div_expr: ('*' | '/') INDENT expr__ expr__ DEDENT;
add_sub_expr: ('+' | '-') INDENT expr__ expr__ DEDENT;
