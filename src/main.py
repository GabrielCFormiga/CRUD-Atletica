from database import conecta, desconecta
from psycopg2 import Error
from datetime import datetime, timedelta
from decimal import Decimal

import relatorio
import venda
import clientes
import produtos
import vendedores

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
            print("4. Gerenciar Vendedores")
            print("5. Relatórios")
            print("6. Sair")
            
            opcao = input("\nEscolha uma opção: ")
            
            if opcao == "1":
                clientes.menu_clientes(conn)
            elif opcao == "2":
                produtos.menu_produtos(conn)
            elif opcao == "3":
                venda.menu_vendas(conn)
            elif opcao == "4":
                vendedores.menu_vendedores(conn)
            elif opcao == "5":
                relatorio.menu_relatorios(conn)
            elif opcao == "6":
                print("Saindo do sistema...")
                desconecta(conn)
                break
            else:
                print("Opção inválida. Tente novamente.")
    return None

if __name__ == "__main__":
    main()