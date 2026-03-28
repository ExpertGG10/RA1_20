import main

assert main.parseExpressao("(3.14 2.0 +)") == ['(', '3.14', '2.0', '+', ')']
assert main.parseExpressao("(20 3 //)") == ['(', '20', '3', '//', ')']
assert main.parseExpressao("(5 RES)") == ['(', '5', 'RES', ')']
assert main.parseExpressao("(10.5 MEM)") == ['(', '10.5', 'MEM', ')']

try:
    main.parseExpressao("(3.14 2.0 &)")
    assert False
except main.ErroLexico:
    pass

try:
    main.parseExpressao("((1 2 +)")
    assert False
except main.ErroLexico:
    pass

print("Testes lexico: OK")
