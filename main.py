#!/usr/bin/env python3
import sys
import re


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
    Retorna: (lista de instrucoes, dicionario de constantes)
    RES e identificadores em maiusculas acessam memoria.
    Um identificador isolado como (MEM) gera leitura.
    Um valor seguido de identificador como (42 MEM) gera escrita.
    """
    linhas = []
    pilha = []
    reg_count = 0
    mem_vars = {}
    constantes = {}

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
                linhas.append(f"    @ Modulo sem BL: a - b * floor(a/b)")
                linhas.append(f"    VDIV.F64 d31, {reg_a}, {reg_b}")
                linhas.append("    VCVT.S32.F64 s30, d31")
                linhas.append("    VCVT.F64.S32 d31, s30")
                linhas.append(f"    VMUL.F64 d31, d31, {reg_b}")
                linhas.append(f"    VSUB.F64 {reg_dest}, {reg_a}, d31")
            elif token == '^':
                linhas.append(f"    @ Potencia sem BL: converte expoente para inteiro")
                linhas.append(f"    VCVT.S32.F64 s30, {reg_b}")
                linhas.append("    VMOV r0, s30")
                linhas.append(f"    @ Verifica se expoente e zero")
                linhas.append("    CMP r0, #0")
                linhas.append(f"    BLE pow_done_{reg_count}")
                linhas.append(f"    @ Inicializa resultado = base")
                linhas.append(f"    VMOV.F64 {reg_dest}, {reg_a}")
                linhas.append(f"    @ Loop: multiplica base-1 vezes")
                linhas.append("    SUB r0, r0, #1")
                linhas.append(f"    CMP r0, #0")
                linhas.append(f"    BLE pow_done_{reg_count}")
                linhas.append(f"pow_loop_{reg_count}:")
                linhas.append(f"    VMUL.F64 {reg_dest}, {reg_dest}, {reg_a}")
                linhas.append("    SUBS r0, r0, #1")
                linhas.append(f"    BNE pow_loop_{reg_count}")
                linhas.append(f"pow_done_{reg_count}:")

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
            constantes[const_label] = valor
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

    return linhas, constantes


def exibirResultados(numero_linha, tokens, estrutura, memoria, historico, num_instrucoes):
    print(f"Linha {numero_linha}:")
    print(f"  Tokens: {tokens}")
    print(f"  Estrutura: {estrutura}")
    print(f"  Memoria: {memoria}")
    print(f"  Historico: {historico}")
    print("  Assembly gerado: sim")
    if num_instrucoes > 0:
        print(f"  Linhas de assembly: {num_instrucoes}")


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
    todas_instrucoes = []
    todas_constantes = {}
    const_counter = 0

    with open("resultados.txt", "w", encoding="utf-8") as arquivo_resultados:
        for numero_linha, linha in enumerate(linhas, start=1):
            if not linha:
                continue

            try:
                tokens = parseExpressao(linha)
                estrutura, memoria, historico = executarExpressao(tokens)
                instrucoes, constantes = gerarAssembly(tokens)
                
                # Rearranja labels de constante para evitar duplicatas
                mapa_constantes = {}
                for label, valor in constantes.items():
                    novo_label = f"const_{const_counter}"
                    const_counter += 1
                    mapa_constantes[label] = novo_label
                    todas_constantes[novo_label] = valor
                
                # Substitui os labels antigos pelos novos nas instrucoes com word boundaries
                instrucoes_ajustadas = []
                for instr in instrucoes:
                    for label_antigo, label_novo in mapa_constantes.items():
                        # Usa regex com word boundaries para evitar substituir substrings
                        instr = re.sub(r'\b' + re.escape(label_antigo) + r'\b', label_novo, instr)
                    instrucoes_ajustadas.append(instr)
                
                todas_instrucoes.append(f"; Linha {numero_linha}")
                todas_instrucoes.extend(instrucoes_ajustadas)
                todas_instrucoes.append("")
                
                arquivo_resultados.write(f"Linha {numero_linha}: {tokens}\n")
                exibirResultados(numero_linha, tokens, estrutura, memoria, historico, len(instrucoes))
            except (ErroLexico, ValueError) as erro:
                mensagem = f"Linha {numero_linha}: erro - {erro}"
                print(mensagem)
                arquivo_resultados.write(mensagem + "\n")

    # Constroi o arquivo assembly final com estrutura correta
    assembly_final = []
    assembly_final.append(".text")
    assembly_final.append(".align 4")
    assembly_final.append(".global main")
    assembly_final.append("main:")
    assembly_final.append("")
    assembly_final.extend(todas_instrucoes)
    assembly_final.append("    BX LR")
    assembly_final.append("")
    assembly_final.append(".data")
    assembly_final.append("memoria_base: .space 256")
    assembly_final.append("historico_base: .space 256")
    assembly_final.append("historico_topo: .word 0")
    
    for label, valor in todas_constantes.items():
        assembly_final.append(f"{label}: .double {valor}")

    with open("assembly_gerado.txt", "w", encoding="utf-8") as arquivo_assembly:
        arquivo_assembly.write("\n".join(assembly_final))
    
    print("Assembly salvo em assembly_gerado.txt")

    print("Assembly salvo em assembly_gerado.txt")


if __name__ == "__main__":
    main()