from database import conecta, desconecta
from psycopg2 import Error
from datetime import datetime, timedelta
from decimal import Decimal

from relatorio import menu_relatorios
from venda import menu_vendas

############################################################################################################
# MAIN
############################################################################################################

conn = None

def main():
    global conn
    conn = conecta()
    if conn is not None:
        while True:
            print("\n=== SISTEMA DA ATLÉTICA COMPILADA ===")
            print("1. Gerenciar Clientes")
            print("2. Gerenciar Produtos")
            print("3. Gerenciar Vendas")
            print("4. Relatórios")
            print("5. Sair")
            
            opcao = input("\nEscolha uma opção: ")
            
            if opcao == "1":
                menu_clientes()
            elif opcao == "2":
                menu_produtos()
            elif opcao == "3":
                menu_vendas(conn)
            elif opcao == "4":
                menu_relatorios(conn)
            elif opcao == "5":
                print("Saindo do sistema...")
                desconecta(conn)
                break
            else:
                print("Opção inválida. Tente novamente.")
    return None

if __name__ == "__main__":
    main()