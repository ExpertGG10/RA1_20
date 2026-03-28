#!/usr/bin/env python3
import sys


class ErroLexico(ValueError):
    pass


def caractere_atual(contexto):
    if contexto["indice"] >= len(contexto["linha"]):
        return None
    return contexto["linha"][contexto["indice"]]


def proximo_caractere(contexto):
    proximo_indice = contexto["indice"] + 1
    if proximo_indice >= len(contexto["linha"]):
        return None
    return contexto["linha"][proximo_indice]


def avancar(contexto):
    contexto["indice"] += 1


def adicionar_token(contexto, token):
    contexto["tokens"].append(token)


def delimitador_valido(caractere):
    if caractere is None:
        return True
    return caractere.isspace() or caractere in "()+-*/%^"


def validar_balanceamento(contexto):
    if contexto["parenteses_abertos"] != 0:
        raise ErroLexico("Parenteses desbalanceados")


def estado_inicial(contexto):
    caractere = caractere_atual(contexto)

    if caractere is None:
        validar_balanceamento(contexto)
        return None

    if caractere.isspace():
        avancar(contexto)
        return estado_inicial

    if caractere == '(':
        contexto["parenteses_abertos"] += 1
        adicionar_token(contexto, caractere)
        avancar(contexto)
        return estado_inicial

    if caractere == ')':
        if contexto["parenteses_abertos"] == 0:
            raise ErroLexico("Parenteses desbalanceados")
        contexto["parenteses_abertos"] -= 1
        adicionar_token(contexto, caractere)
        avancar(contexto)
        return estado_inicial

    if caractere in ['+', '*', '%', '^']:
        adicionar_token(contexto, caractere)
        avancar(contexto)
        return estado_inicial

    if caractere == '/':
        contexto["lexema"] = "/"
        avancar(contexto)
        return estado_barra

    if caractere == '-':
        if proximo_caractere(contexto) is not None and proximo_caractere(contexto).isdigit():
            contexto["lexema"] = "-"
            avancar(contexto)
            return estado_numero
        adicionar_token(contexto, caractere)
        avancar(contexto)
        return estado_inicial

    if caractere.isdigit():
        contexto["lexema"] = ""
        return estado_numero

    if caractere.isupper():
        contexto["lexema"] = ""
        return estado_identificador

    raise ErroLexico(f"Caractere desconhecido: {caractere}")


def estado_barra(contexto):
    caractere = caractere_atual(contexto)
    if caractere == '/':
        adicionar_token(contexto, "//")
        avancar(contexto)
        return estado_inicial

    adicionar_token(contexto, "/")
    return estado_inicial


def estado_numero(contexto):
    while True:
        caractere = caractere_atual(contexto)
        if caractere is None:
            break
        if caractere.isdigit():
            contexto["lexema"] += caractere
            avancar(contexto)
            continue
        if caractere == '.':
            contexto["lexema"] += caractere
            avancar(contexto)
            return estado_fracao
        break

    if contexto["lexema"] in ["", "-"]:
        raise ErroLexico("Numero malformado")

    caractere = caractere_atual(contexto)
    if not delimitador_valido(caractere):
        raise ErroLexico(f"Numero malformado: {contexto['lexema']}{caractere}")

    adicionar_token(contexto, contexto["lexema"])
    contexto["lexema"] = ""
    return estado_inicial


def estado_fracao(contexto):
    caractere = caractere_atual(contexto)
    if caractere is None or not caractere.isdigit():
        raise ErroLexico("Numero real malformado")

    while True:
        caractere = caractere_atual(contexto)
        if caractere is None or not caractere.isdigit():
            break
        contexto["lexema"] += caractere
        avancar(contexto)

    caractere = caractere_atual(contexto)
    if not delimitador_valido(caractere):
        raise ErroLexico(f"Numero real malformado: {contexto['lexema']}{caractere}")

    adicionar_token(contexto, contexto["lexema"])
    contexto["lexema"] = ""
    return estado_inicial


def estado_identificador(contexto):
    while True:
        caractere = caractere_atual(contexto)
        if caractere is None or not caractere.isupper():
            break
        contexto["lexema"] += caractere
        avancar(contexto)

    caractere = caractere_atual(contexto)
    if not delimitador_valido(caractere):
        raise ErroLexico(f"Identificador invalido: {contexto['lexema']}{caractere}")

    adicionar_token(contexto, contexto["lexema"])
    contexto["lexema"] = ""
    return estado_inicial


def parseExpressao(linha):
    contexto = {
        "linha": linha,
        "indice": 0,
        "tokens": [],
        "lexema": "",
        "parenteses_abertos": 0,
    }

    estado = estado_inicial
    while estado is not None:
        estado = estado(contexto)

    return contexto["tokens"]
            
            

def executarExpressao(expressao):
    pass

def gerarAssembly(expressao):
    pass

def exibirResultados(resultado):
    pass

def lerArquivo():
    if len(sys.argv) != 2:
        print("Escreva no formato: python main.py teste1.txt")
        sys.exit(1)

    nome_arquivo = sys.argv[1]

    try:
        linhas = []
        with open(nome_arquivo, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                linhas.append(linha)
            return linhas
        
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {nome_arquivo}")

def main():
    linhas = lerArquivo()
    print(f"Resultados:{linhas}")
    with open("resultados.txt", "w", encoding="utf-8") as f:
            for i in linhas:
                try:
                    f.write(f"{parseExpressao(i)}\n")
                except ErroLexico as erro:
                    f.write(f"Erro lexico: {erro}\n")


    
    

if __name__ == "__main__":
    main()