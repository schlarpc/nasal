import lark

parser = lark.Lark(r"""

COMMENT: "#" /[^\n]/*

%ignore /\s+/
%ignore COMMENT
_IF: "if"
_LPAREN: "("
_LBRACE: "{"
_RPAREN: ")"
_RBRACE: "}"
_COLON: ":"
_COMMA: ","
_SEMICOLON: ";"
IDENT: /(::|[_a-z])([_a-z0-9]*::[_a-z0-9]+)*[_a-z0-9]*/i
STRING: /"[^"]*"/m
INT_DEC: /(0|[1-9][0-9]*)/
INT_OCT: /0[0-7]+/



start: statement +

statement : compound
          | simple

simple : call

?call : call_exp _SEMICOLON

call_exp : lval _LPAREN args _RPAREN

args : (arg (_COMMA arg)*)?

arg : expr
    | ident_ex _COLON expr

compound : if_
         | block

if_ : _IF _LPAREN expr _RPAREN statement

block : _LBRACE statements _RBRACE

statements: statement +

expr : lval
     | string
     | int

lval : ident

?ident: IDENT

int: INT_DEC
   | INT_OCT

ident_ex : ident

string : STRING



""")
import ast, pprint
class Transformer(lark.Transformer):
    def string(self, match):
        return ast.literal_eval(match[0].value)
        print(match)
        return match

    def int(self, matches):
        if matches[0].type == 'INT_OCT':
            return ast.literal_eval('0o' + matches[0].value[1:])
        return ast.literal_eval(matches[0].value)

with open('template.nasl', 'r') as f:
    tree = parser.parse(f.read())
    print(Transformer().transform(tree).pretty())