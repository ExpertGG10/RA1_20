import main

testes = ["(-3 + 4) * 5", "6.6.6 + 3 * 1", "((1 + 2) * (3 - 4)) / 5"]



for expressao in testes:
    resultado = main.parseExpressao(expressao)
    print(f"Expressao: {expressao} -> Tokens: {resultado}")

