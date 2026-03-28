import main

tokens1 = ['(', '3.14', '2.0', '+', ')']
assembly = main.gerarAssembly(tokens1)

print("=== Teste gerarAssembly ===")
print(assembly)
print()

tokens2 = ['(', '10', '5', '*', ')']
assembly2 = main.gerarAssembly(tokens2)
print(assembly2)
print()

assert ".text" in assembly
assert "VADD" in assembly or "VSUB" in assembly or "VMUL" in assembly
assert "BX LR" in assembly

print("Testes gerarAssembly: OK")
