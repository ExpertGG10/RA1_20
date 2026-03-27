#!/usr/bin/env python3
import sys


def parseExpressao(linnha):
    resultado = []
    digito = ""
    operacao = ""
    for i in linnha:
        if i in ['(', ')', '+', '-', '*', '/', "^", "%"]:
            resultado.append(i)
        elif i in ['M', 'E', 'R', 'S']:
            operacao += i
            if operacao in ["MEM", "RES"]:
                resultado.append(operacao)
                operacao = ""
        elif i in ["1","2","3","4","5","6","7","8","9","0"] or (i == '.' and digito.find('.') == -1):
            digito += i
        elif i.isspace():
            if digito:
                resultado.append(digito)
                digito = ""
            if operacao:
                print("Operação desconhecida:", operacao)
                return None
        else:
            print("Caractere desconhecido:", i)
            return None
    if digito:
        resultado.append(digito)
    if operacao:
        print("Operação desconhecida:", operacao)
        return None
    return resultado
            
            

def executarExpressao(expressao):
    pass

def gerarAssembly(expressao):
    pass

def exibirResultados(resultado):
    pass

def main():
    pass

if __name__ == "__main__":
    main()