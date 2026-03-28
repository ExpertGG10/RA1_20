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
        contexto["token"] = "/"
        avancar(contexto)
        return estado_barra

    if caractere == '-':
        if proximo_caractere(contexto) is not None and proximo_caractere(contexto).isdigit():
            contexto["token"] = "-"
            avancar(contexto)
            return estado_numero
        adicionar_token(contexto, caractere)
        avancar(contexto)
        return estado_inicial

    if caractere.isdigit():
        contexto["token"] = ""
        return estado_numero

    if caractere.isupper():
        contexto["token"] = ""
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
            contexto["token"] += caractere
            avancar(contexto)
            continue
        if caractere == '.':
            contexto["token"] += caractere
            avancar(contexto)
            return estado_fracao
        break

    if contexto["token"] in ["", "-"]:
        raise ErroLexico("Numero malformado")

    caractere = caractere_atual(contexto)
    if not delimitador_valido(caractere):
        raise ErroLexico(f"Numero malformado: {contexto['token']}{caractere}")

    adicionar_token(contexto, contexto["token"])
    contexto["token"] = ""
    return estado_inicial


def estado_fracao(contexto):
    caractere = caractere_atual(contexto)
    if caractere is None or not caractere.isdigit():
        raise ErroLexico("Numero real malformado")

    while True:
        caractere = caractere_atual(contexto)
        if caractere is None or not caractere.isdigit():
            break
        contexto["token"] += caractere
        avancar(contexto)

    caractere = caractere_atual(contexto)
    if not delimitador_valido(caractere):
        raise ErroLexico(f"Numero real malformado: {contexto['token']}{caractere}")

    adicionar_token(contexto, contexto["token"])
    contexto["token"] = ""
    return estado_inicial


def estado_identificador(contexto):
    while True:
        caractere = caractere_atual(contexto)
        if caractere is None or not caractere.isupper():
            break
        contexto["token"] += caractere
        avancar(contexto)

    caractere = caractere_atual(contexto)
    if not delimitador_valido(caractere):
        raise ErroLexico(f"Identificador invalido: {contexto['token']}{caractere}")

    adicionar_token(contexto, contexto["token"])
    contexto["token"] = ""
    return estado_inicial


def parseExpressao(linha):
    contexto = {
        "linha": linha,
        "indice": 0,
        "tokens": [],
        "token": "",
        "parenteses_abertos": 0,
    }

    estado = estado_inicial
    while estado is not None:
        estado = estado(contexto)

    return contexto["tokens"]
            
            

def executarExpressao(tokens):
    memoria = {}
    historico = []
    pilha = []
    idx = 0

    while idx < len(tokens):
        token = tokens[idx]

        if token == '(':
            idx += 1
            continue

        if token == ')':
            if len(pilha) != 1:
                raise ValueError(f"Parenteses fecham com pilha incorreta")
            item = pilha.pop()
            historico.append(item)
            return item, memoria, historico

        if token in ['+', '-', '*', '/', '//', '%', '^']:
            if len(pilha) < 2:
                raise ValueError(f"Operador {token} requer dois operandos")
            pilha.pop()
            pilha.pop()
            pilha.append(f"({token})")
            idx += 1
            continue

        if token == 'RES':
            if len(pilha) == 0:
                raise ValueError("RES sem argumento")
            pilha.pop()
            pilha.append("(RES)")
            idx += 1
            continue

        if token == 'MEM':
            if len(pilha) == 0:
                raise ValueError("MEM sem identificador")
            nome_var = pilha.pop()
            pilha.append(f"(MEM {nome_var})")
            idx += 1
            continue

        if token.isupper() and token not in ['RES', 'MEM']:
            pilha.append(token)
            idx += 1
            continue

        try:
            float(token)
            pilha.append(token)
        except ValueError:
            raise ValueError(f"Token invalido: {token}")

        idx += 1

    raise ValueError("Expressao incompleta")


def gerarAssembly(tokens):
    """
    Gera codigo ARM v7 VFP a partir de tokens RPN.
    Usa registradores s0-s31 para ponto flutuante (IEEE 754 64-bit).
    """
    linhas = []
    pilha_regs = []
    contador_reg = 0
    contador_label = 0
    memoria_vars = {}
    
    linhas.append(".text")
    linhas.append(".align 4")
    linhas.append("")
    
    for token in tokens:
        if token == '(':
            continue
            
        if token == ')':
            break
            
        if token in ['+', '-', '*', '/', '//', '%', '^']:
            if len(pilha_regs) < 2:
                raise ValueError(f"Operador {token} sem operandos suficientes")
            
            reg_b = pilha_regs.pop()
            reg_a = pilha_regs.pop()
            reg_dest = f"s{contador_reg}"
            contador_reg += 1
            
            if token == '+':
                linhas.append(f"    VADD.F64 {reg_dest}, {reg_a}, {reg_b}")
            elif token == '-':
                linhas.append(f"    VSUB.F64 {reg_dest}, {reg_a}, {reg_b}")
            elif token == '*':
                linhas.append(f"    VMUL.F64 {reg_dest}, {reg_a}, {reg_b}")
            elif token == '/':
                linhas.append(f"    VDIV.F64 {reg_dest}, {reg_a}, {reg_b}")
            elif token == '//':
                linhas.append(f"    VDIV.F64 {reg_dest}, {reg_a}, {reg_b}")
                linhas.append(f"    VCVT.S32.F64 d0, {reg_dest}")
                linhas.append(f"    VCVT.F64.S32 {reg_dest}, d0")
            elif token == '%':
                linhas.append(f"    VCVT.S32.F64 r0, {reg_a}")
                linhas.append(f"    VCVT.S32.F64 r1, {reg_b}")
                linhas.append(f"    MOD r0, r0, r1")
                linhas.append(f"    VCVT.F64.S32 {reg_dest}, r0")
            elif token == '^':
                linhas.append(f"    MOV r0, #{reg_a}")
                linhas.append(f"    MOV r1, #{reg_b}")
                linhas.append(f"    BL pow")
                linhas.append(f"    VMOV {reg_dest}, r0")
            
            pilha_regs.append(reg_dest)
            
        elif token == 'RES':
            if len(pilha_regs) > 0:
                pilha_regs.pop()
            pilha_regs.append("s0")
            
        elif token == 'MEM':
            if len(pilha_regs) > 0:
                var_name = pilha_regs.pop()
                if var_name not in memoria_vars:
                    memoria_vars[var_name] = f"_var_{len(memoria_vars)}"
                pilha_regs.append(f"s{contador_reg}")
                contador_reg += 1
            
        else:
            try:
                valor = float(token)
                reg_dest = f"s{contador_reg}"
                contador_reg += 1
                
                linhas.append(f"    VLDR.F64 {reg_dest}, =#{valor}")
                pilha_regs.append(reg_dest)
                
            except ValueError:
                pass
    
    linhas.append("")
    linhas.append("    BX LR")
    
    return "\n".join(linhas)


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