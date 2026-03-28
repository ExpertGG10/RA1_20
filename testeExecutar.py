import main

tokens1 = ['(', '3.14', '2.0', '+', ')']
item, mem, hist = main.executarExpressao(tokens1)
assert len(hist) == 1

tokens2 = ['(', '20', '3', '//', ')']
item, mem, hist = main.executarExpressao(tokens2)
assert len(hist) == 1

tokens3 = ['(', '10', '5', '*', ')']
item, mem, hist = main.executarExpressao(tokens3)
assert len(hist) == 1

print("Testes executar: OK")
