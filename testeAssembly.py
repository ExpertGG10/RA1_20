import main

tokens1 = ['(', '3.14', '2.0', '+', ')']
assembly = main.gerarAssembly(tokens1)
print("=== Teste adição ===")
print(assembly)
assert "const_0: .double 3.14" in assembly
assert "const_1: .double 2.0" in assembly
assert "LDR r0, =const_0" in assembly
assert "VLDR d0, [r0]" in assembly
assert "VADD.F64" in assembly

tokens2 = ['(', '42', 'MEM', ')']
assembly2 = main.gerarAssembly(tokens2)
print("=== Teste escrita em MEM ===")
print(assembly2)
assert "const_0: .double 42.0" in assembly2
assert "VSTR d0, [r0]" in assembly2


tokens3 = ['(', 'MEM', ')']
assembly3 = main.gerarAssembly(tokens3)
print("=== Teste leitura de MEM ===")
print(assembly3)
assert "VLDR d0, [r0]" in assembly3


tokens4 = ['(', '5', 'RES', ')']
assembly4 = main.gerarAssembly(tokens4)
print("=== Teste RES ===")
print(assembly4)
assert "historico_base" in assembly4
assert "VLDR d1, [r2]" in assembly4
