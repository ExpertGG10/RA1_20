import main, sys

if len(sys.argv) != 2:
        print("Escreva no formato: python main.py teste1.txt")
        sys.exit(1)

nome_arquivo = sys.argv[1]

try:
    nmr_linha = 0
    with open(nome_arquivo, "r", encoding="utf-8") as f:
        for linha in f:
            nmr_linha += 1
            linha = linha.strip()
            if not linha:
                continue
            tokens = main.parseExpressao(linha)
            print(f"Linha {nmr_linha}: {tokens}")
except FileNotFoundError:
    print(f"Arquivo não encontrado: {nome_arquivo}")