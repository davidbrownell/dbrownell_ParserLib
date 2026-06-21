grammar ignore_whitespace;

INT : [0-9]+ ;
WS : [ \t\n\r]+ -> skip ;

start__ : expr (';' expr)* EOF;
expr : atom | unary_expr | expr '**' expr | expr ('*' | '/') expr | expr ('+' | '-') expr | grouped_expr | atom;
unary_expr: ('+' | '-') expr;
grouped_expr: '(' expr ')';
atom : INT;
