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
            
            
def proximo_token_significativo(tokens, indice_atual):
    for indice in range(indice_atual + 1, len(tokens)):
        if tokens[indice] not in ['(', ')']:
            return tokens[indice]
    return None


def executarExpressao(tokens):
    memoria = {}
    historico = []
    pilha = []

    for indice, token in enumerate(tokens):
        if token in ['(', ')']:
            continue

        if token in ['+', '-', '*', '/', '//', '%', '^']:
            if len(pilha) < 2:
                raise ValueError(f"Operador {token} requer dois operandos")
            pilha.pop()
            pilha.pop()
            pilha.append(f"({token})")
            continue

        if token == 'RES':
            if len(pilha) == 0:
                raise ValueError("RES sem argumento")
            pilha.pop()
            pilha.append("(RES)")
            continue

        if token.isupper() and token != 'RES':
            proximo = proximo_token_significativo(tokens, indice)
            if proximo is None and len(pilha) >= 1:
                valor = pilha.pop()
                memoria[token] = valor
                pilha.append(f"(STORE {token})")
            else:
                pilha.append(f"(LOAD {token})")
            continue

        try:
            float(token)
            pilha.append(token)
        except ValueError:
            raise ValueError(f"Token invalido: {token}")

    if len(pilha) != 1:
        raise ValueError("Expressao incompleta")

    item = pilha.pop()
    historico.append(item)
    return item, memoria, historico


def gerarAssembly(tokens):
    """
    Gera codigo ARMv7 a partir dos tokens.
    RES e identificadores em maiusculas acessam memoria.
    Um identificador isolado como (MEM) gera leitura.
    Um valor seguido de identificador como (42 MEM) gera escrita.
    """
    linhas = [
        ".text",
        ".align 4",
        ".global main",
        "main:",
        ""
    ]

    pilha = []
    reg_count = 0
    mem_vars = {}
    constantes = []

    for indice, token in enumerate(tokens):
        if token in ['(', ')']:
            continue

        if token in ['+', '-', '*', '/', '//', '%', '^']:
            if len(pilha) < 2:
                raise ValueError(f"Operador {token} sem operandos")

            reg_b = pilha.pop()
            reg_a = pilha.pop()
            reg_dest = f"d{reg_count}"
            reg_count += 1

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
                linhas.append(f"    VCVT.S32.F64 s30, {reg_dest}")
                linhas.append(f"    VCVT.F64.S32 {reg_dest}, s30")
            elif token == '%':
                linhas.append(f"    VCVT.S32.F64 s30, {reg_a}")
                linhas.append(f"    VCVT.S32.F64 s31, {reg_b}")
                linhas.append("    VMOV r0, s30")
                linhas.append("    VMOV r1, s31")
                linhas.append("    BL __aeabi_idivmod")
                linhas.append("    VMOV s30, r1")
                linhas.append(f"    VCVT.F64.S32 {reg_dest}, s30")
            elif token == '^':
                linhas.append(f"    VMOV r0, r1, {reg_a}")
                linhas.append(f"    VMOV r2, r3, {reg_b}")
                linhas.append("    BL pow")
                linhas.append(f"    VMOV {reg_dest}, r0, r1")

            pilha.append(reg_dest)
            continue

        if token == 'RES':
            if len(pilha) == 0:
                raise ValueError("RES sem argumento")

            indice_reg = pilha.pop()
            reg_dest = f"d{reg_count}"
            reg_count += 1

            linhas.append(f"    VCVT.S32.F64 s30, {indice_reg}")
            linhas.append("    VMOV r0, s30")
            linhas.append("    LDR r2, =historico_base")
            linhas.append("    LDR r3, =historico_topo")
            linhas.append("    LDR r3, [r3]")
            linhas.append("    SUB r3, r3, r0")
            linhas.append("    LSL r3, r3, #3")
            linhas.append("    ADD r2, r2, r3")
            linhas.append(f"    VLDR {reg_dest}, [r2]")

            pilha.append(reg_dest)
            continue

        try:
            valor = float(token)
            reg_dest = f"d{reg_count}"
            reg_count += 1
            const_label = f"const_{len(constantes)}"
            constantes.append((const_label, valor))
            linhas.append(f"    LDR r0, ={const_label}")
            linhas.append(f"    VLDR {reg_dest}, [r0]")
            pilha.append(reg_dest)
            continue
        except ValueError:
            pass

        if token.isupper() and token != 'RES':
            if token not in mem_vars:
                mem_vars[token] = len(mem_vars) * 8

            offset = mem_vars[token]
            proximo = proximo_token_significativo(tokens, indice)

            if proximo is None and len(pilha) >= 1:
                valor_reg = pilha.pop()
                linhas.append("    LDR r0, =memoria_base")
                linhas.append(f"    ADD r0, r0, #{offset}")
                linhas.append(f"    VSTR {valor_reg}, [r0]")
                pilha.append(valor_reg)
            else:
                reg_dest = f"d{reg_count}"
                reg_count += 1
                linhas.append("    LDR r0, =memoria_base")
                linhas.append(f"    ADD r0, r0, #{offset}")
                linhas.append(f"    VLDR {reg_dest}, [r0]")
                pilha.append(reg_dest)
            continue

        raise ValueError(f"Token invalido no assembly: {token}")

    linhas.append("")
    linhas.append("    BX LR")
    linhas.append("")
    linhas.append(".data")
    linhas.append("memoria_base: .space 256")
    linhas.append("historico_base: .space 256")
    linhas.append("historico_topo: .word 0")

    for const_label, valor in constantes:
        linhas.append(f"{const_label}: .double {valor}")

    return "\n".join(linhas)


def exibirResultados(numero_linha, tokens, estrutura, memoria, historico, assembly):
    print(f"Linha {numero_linha}:")
    print(f"  Tokens: {tokens}")
    print(f"  Estrutura: {estrutura}")
    print(f"  Memoria: {memoria}")
    print(f"  Historico: {historico}")
    print("  Assembly gerado: sim")
    if assembly:
        print(f"  Linhas de assembly: {len(assembly.splitlines())}")


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
    blocos_assembly = []

    with open("resultados.txt", "w", encoding="utf-8") as arquivo_resultados:
        for numero_linha, linha in enumerate(linhas, start=1):
            if not linha:
                continue

            try:
                tokens = parseExpressao(linha)
                estrutura, memoria, historico = executarExpressao(tokens)
                assembly = gerarAssembly(tokens)

                arquivo_resultados.write(f"Linha {numero_linha}: {tokens}\n")
                blocos_assembly.append(f"; Linha {numero_linha}\n{assembly}")
                exibirResultados(numero_linha, tokens, estrutura, memoria, historico, assembly)
            except (ErroLexico, ValueError) as erro:
                mensagem = f"Linha {numero_linha}: erro - {erro}"
                print(mensagem)
                arquivo_resultados.write(mensagem + "\n")

    with open("assembly_gerado.txt", "w", encoding="utf-8") as arquivo_assembly:
        arquivo_assembly.write("\n\n".join(blocos_assembly))

    print("Assembly salvo em assembly_gerado.txt")


if __name__ == "__main__":
    main()