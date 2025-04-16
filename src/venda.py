from psycopg2 import Error
from decimal import Decimal
from datetime import datetime, timedelta
import os

from clientes import buscar_cliente_por_matricula
from produtos import buscar_produto_por_id, listar_produtos, validar_quantidade
from vendedores import buscar_vendedor_por_matricula

STATUS_VENDA = {
    'PENDENTE': 'Pendente de autorização',
    'AUTORIZADA': 'Autorizada',
    'CANCELADA': 'Cancelada'
}

FORMAS_PAGAMENTO = ['Pix', 'Dinheiro', 'Boleto', 'Cartão', 'Berries']

############################################################################################################
# MÉTODOS DE VALIDAÇÃO
############################################################################################################

def validar_forma_pagamento(forma):
    return forma.upper() in [fp.upper() for fp in FORMAS_PAGAMENTO]

############################################################################################################
# MÉTODOS DE BUSCA
############################################################################################################

def buscar_venda_por_id(conn, venda_id):
    """
    Busca uma venda pelo ID no banco de dados.

    Args:
        venda_id (int): ID da venda a ser buscada.

    Returns:
        tuple or None: Dados da venda se encontrada, ou None se não encontrada ou em caso de erro.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.id, c.nome, v.valor_total, v.data_venda, v.forma_pagamento
            FROM vendas v
            JOIN clientes c ON v.cliente_matricula = c.matricula
            WHERE v.id = %s
        """, (venda_id,))
        venda = cursor.fetchone()
        return venda
    except Error as e:
        print(f"Erro ao buscar venda: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

def verificar_estoque_suficiente(conn, id_produto, quantidade):
    """
    Verifica se há estoque suficiente para o produto.

    Args:
        id_produto (int): ID do produto a ser verificado.
        quantidade (int): Quantidade desejada.

    Returns:
        bool: True se houver estoque suficiente, False caso contrário.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT quantidade FROM produtos WHERE id = %s
        """, (id_produto,))
        resultado = cursor.fetchone()
        return resultado and resultado[0] >= quantidade
    except Error as e:
        print(f"Erro ao verificar estoque: {e}")
        return False
    finally:
        if cursor:
            cursor.close()

def verificar_desconto(conn, matricula):
    """
    Verifica se o cliente tem direito a desconto especial
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM verificar_desconto(%s)", (matricula,))
        resultado = cursor.fetchone()
        
        if resultado:
            return {
                'tem_desconto': resultado[0],
                'motivo': resultado[1],
                'time': resultado[2],
                'cidade': resultado[3],
                'assiste_one_piece': resultado[4]
            }
        return None
        
    except Error as e:
        print(f"Erro ao verificar desconto: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

############################################################################################################
# MÉTODOS CRUD
############################################################################################################

def print_linha(tamanho=70):
    """Imprime uma linha divisória"""
    print("-" * tamanho)

def print_resumo_venda(conn, cliente, forma_pagamento, itens, valor_total, desconto_info=None): 
    # Cabeçalho
    print("\n" + "=" * 70)
    print(" RESUMO DA VENDA ".center(70, "~"))
    print("=" * 70)
    
    # Informações básicas
    print(f"\n{'Cliente:':<15} {cliente[1]}")
    print(f"{'Pagamento:':<15} {forma_pagamento}")
    
    # Tabela de itens
    print("\n" + " ITENS ".center(70, "-"))
    print(f"{'Produto':<30} {'Qtd':>5} {'Valor':>10} {'Total':>10}")
    print_linha()
    
    for item in itens:
        produto = buscar_produto_por_id(conn, item['id_produto'])
        subtotal = Decimal(item['quantidade']) * item['preco_unitario']
        print(
            f"{produto[1][:28]:<30} "
            f"{item['quantidade']:>5}x "
            f"R${item['preco_unitario']:>7.2f} "
            f"R${subtotal:>8.2f}"
        )
    
    # Totais
    print_linha()
    print(f"{'SUBTOTAL:':<40} R${valor_total:>8.2f}")
    
    # Descontos (se aplicável)
    if desconto_info and desconto_info['tem_desconto']:
        desconto = valor_total * Decimal('0.10')  # 10% de desconto
        valor_total -= desconto
        print(f"{'DESCONTO (' + desconto_info['motivo'] + '):':<40} -R${desconto:>7.2f}")
        print_linha()
        print(f"{'TOTAL FINAL:':<40} R${valor_total:>8.2f}")
    else:
        print(f"{'TOTAL:':<40} R${valor_total:>8.2f}")
    
    print("=" * 70 + "\n")

def registrar_venda(conn):
    """
    Fluxo:
    - Solicita matrícula do cliente e valida.
    - Solicita forma de pagamento e valida.
    - Permite adicionar itens à venda, validando produto e quantidade.
    - Calcula o total da venda e aplica desconto.
    - Insere a venda e os itens no banco de dados.
    """
    print("\n--- Registro de Nova Venda ---")
    
    # Validação do cliente
    while True:
        matricula = input("\nMatrícula do cliente: ").strip()
        cliente = buscar_cliente_por_matricula(conn, matricula)
        
        if not cliente:
            print("\nCliente não encontrado!")
            continuar = input("\nDeseja tentar novamente? (S/N): ").upper()
            if continuar != 'S':
                return None
            continue
        
        print(f"\nCliente: {cliente[1]}")
        break

    # Verificação de desconto
    desconto_info = verificar_desconto(conn, matricula)
    if desconto_info:
        print("\nInformações para desconto:")
        print(f"Time: {desconto_info['time']}")
        print(f"Cidade: {desconto_info['cidade']}")
        print(f"Assiste One Piece: {'Sim' if desconto_info['assiste_one_piece'] else 'Não'}")
    
    # Validação da forma de pagamento
    while True:
        print("\nFormas de pagamento disponíveis:")
        for i, forma in enumerate(FORMAS_PAGAMENTO, 1):
            print(f"{i}. {forma}")
        
        try:
            opcao = int(input("Escolha o número da forma de pagamento: "))
            if 1 <= opcao <= len(FORMAS_PAGAMENTO):
                forma_pagamento = FORMAS_PAGAMENTO[opcao-1]
                break
            print("Opção inválida! Escolha um número da lista.")
        except ValueError:
            print("Entrada inválida! Digite apenas o número correspondente.")
    
    # Seleção do vendedor
    while True:
        matricula_vendedor = input("\nMatrícula do vendedor: ").strip()
        vendedor = buscar_vendedor_por_matricula(conn, matricula_vendedor)
        
        if not vendedor:
            print("Vendedor não encontrado!")
            continuar = input("Deseja tentar novamente? (S/N): ").upper()
            if continuar != 'S':
                return None
            continue
            
        if not vendedor[4]:  # Verifica se vendedor está ativo (campo ativo)
            print("Vendedor inativo! Não pode realizar vendas.")
            continuar = input("Deseja tentar outro vendedor? (S/N): ").upper()
            if continuar != 'S':
                return None
            continue
            
        print(f"Vendedor: {vendedor[1]}")
        break
    
    # Cadastro dos itens da venda
    itens = []
    while True:
        print("\n--- Adicionar Item à Venda ---")
        listar_produtos(conn)
        
        # Validação do produto
        while True:
            id_produto = input("\nID do produto (ou 0 para finalizar): ").strip()
            if id_produto == "0":
                break
            
            if not id_produto.isdigit():
                print("ID inválido! Deve ser um número.")
                continue
            
            produto = buscar_produto_por_id(conn, id_produto)
            if not produto:
                print("Produto não encontrado!")
                continue
            
            print(f"\nProduto selecionado: {produto[1]}")
            print(f"Preço unitário: R${produto[3]:.2f}")
            print(f"Estoque disponível: {produto[2]}")
            break
        
        if id_produto == "0":
            if not itens:
                print("Nenhum item adicionado à venda. Operação cancelada.")
                return None
            break
        
        # Validação da quantidade
        while True:
            quantidade = input("Quantidade: ").strip()
            if not validar_quantidade(quantidade):
                print("Quantidade inválida! Deve ser um número inteiro positivo.")
                continue
            
            quantidade = int(quantidade)
            if not verificar_estoque_suficiente(conn, id_produto, quantidade):
                print("Quantidade indisponível em estoque!")
                continue
            
            break
        
        # Adiciona item à venda (convertendo preço para Decimal)
        itens.append({
            'id_produto': id_produto,
            'quantidade': quantidade,
            'preco_unitario': Decimal(str(produto[3]))
        })
        
        print(f"\nItem adicionado: {produto[1]} - {quantidade}x R${produto[3]:.2f}")
        continuar = input("Deseja adicionar mais itens? (S/N): ").upper()
        if continuar != 'S':
            break
    
    # Cálculo do valor total (usando Decimal para todas operações)
    valor_total = sum(Decimal(item['quantidade']) * item['preco_unitario'] for item in itens)

    # Aplicação do desconto especial (se elegível)
    if desconto_info and desconto_info['tem_desconto']:
        desconto = valor_total * Decimal('0.10')  # 10% de desconto
        valor_total -= desconto

    # Resumo da venda
    os.system('cls' if os.name == 'nt' else 'clear')
    print_resumo_venda(conn, cliente, forma_pagamento, itens, valor_total, desconto_info)

    # Confirmação
    confirmacao = input("\nConfirmar venda? (S/N): ").upper()
    if confirmacao != 'S':
        print("\nVenda cancelada!")
        return None
    
    # Registra a venda no banco de dados
    try:
        cursor = conn.cursor()
        
        if desconto_info and desconto_info['tem_desconto']:
            cursor.execute("""
                INSERT INTO vendas (
                    cliente_matricula, valor_total, forma_pagamento, status,
                    desconto_aplicado, motivo_desconto, valor_desconto
                )
                VALUES (%s, %s, %s, 'PENDENTE', TRUE, %s, %s)
                RETURNING id
            """, (
                matricula, 
                float(valor_total), 
                forma_pagamento,
                desconto_info['motivo'],
                float(desconto)
            ))
        else:
            cursor.execute("""
                INSERT INTO vendas (
                    cliente_matricula, valor_total, forma_pagamento, status
                )
                VALUES (%s, %s, %s, 'PENDENTE')
                RETURNING id
            """, (matricula, float(valor_total), forma_pagamento))
        
        venda_id = cursor.fetchone()[0]
        
        # Registra a relação vendedor-venda
        cursor.execute("""
            INSERT INTO vendedor_vendas (vendedor_matricula, id_venda)
            VALUES (%s, %s)
        """, (matricula_vendedor, venda_id))
        
        # Insere os itens da venda e atualiza estoque
        for item in itens:
            cursor.execute("""
                INSERT INTO itens_venda (id_venda, id_produto, quantidade, valor_unitario)
                VALUES (%s, %s, %s, %s)
            """, (venda_id, item['id_produto'], item['quantidade'], float(item['preco_unitario'])))
            
            cursor.execute("""
                UPDATE produtos 
                SET quantidade = quantidade - %s 
                WHERE id = %s
            """, (item['quantidade'], item['id_produto']))
        
        conn.commit()
        print(f"\nVenda registrada com sucesso! ID: {venda_id}")
        print("Status: Pendente de autorização")
        return venda_id
        
    except Error as e:
        conn.rollback()
        print(f"\nErro ao registrar venda: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

def listar_vendas(conn):
    """
    Lista todas as vendas com opções de filtro robustas.
    """
    while True:
        print("\n=== LISTAGEM DE VENDAS ===")
        print("1. Listar todas as vendas")
        print("2. Filtrar por período")
        print("3. Filtrar por cliente")
        print("4. Voltar ao menu anterior")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            try:
                cursor = conn.cursor()
                cursor.execute(""" 
                    SELECT id, cliente_matricula, valor_total, data_venda
                    FROM vendas
                """)
                vendas = cursor.fetchall()

                if vendas:
                    print("\n╭────────────────────────────────────────────────────────────────────────────────────────╮")
                    print(f"│ {'ID':<12} │ {'Cliente':<25} │ {'Valor Total':<25} │ {'Data':<15} │")
                    print("├──────────────┼───────────────────────────┼───────────────────────────┼─────────────────┤")
                    
                    for venda in vendas:
                        id, cliente_matricula, valor_total, data_venda = venda
                        print(f"│ {id:<12} │ {str(cliente_matricula)[:25]:<25} │ {str(valor_total)[:25]:<25} │ {str(data_venda)[:15]:<15} │")
                    
                    print("╰──────────────┴───────────────────────────┴───────────────────────────┴─────────────────╯")
                    print(f"\nTotal de vendas cadastradas: {len(vendas)}")

                    detalhar = input("\nDeseja detalhar alguma venda? (S/N): ").upper()
                    if detalhar == 'S':
                        while True:
                            venda_id = input("\nID da venda a detalhar: ").strip()
                            if not venda_id.isdigit():
                                print("\nID inválido! Deve ser um número.")
                                continue
                            break
                        detalhar_venda(conn, venda_id)
                else:
                    print("\nNenhuma venda cadastrada no sistema.")
            except Error as e:
                print(f"Erro ao listar vendas: {e}")
            finally:
                if cursor:
                    cursor.close()
            return
        elif opcao == "2":
            print("\n--- FILTRAR POR PERÍODO ---")
    
            while True:
                try:
                    data_inicio = input("Data inicial (DD/MM/AAAA): ").strip()
                    data_fim = input("Data final (DD/MM/AAAA): ").strip()
                    
                    data_inicio_dt = datetime.strptime(data_inicio, '%d/%m/%Y')
                    data_fim_dt = datetime.strptime(data_fim, '%d/%m/%Y')
                    
                    if data_fim_dt < data_inicio_dt:
                        print("\nErro: A data final deve ser maior ou igual à data inicial!")
                        continue
                        
                    if (data_fim_dt - data_inicio_dt) > timedelta(days=365):
                        print("\nErro: Período muito longo! O limite é de 1 ano.")
                        continue
                        
                    try:
                        cursor = conn.cursor()
                        cursor.execute(""" 
                            SELECT id, cliente_matricula, valor_total, data_venda
                            FROM vendas
                            WHERE data_venda BETWEEN %s AND %s
                            ORDER BY data_venda
                        """, (data_inicio_dt, data_fim_dt))
                        
                        vendas = cursor.fetchall()

                        if vendas:
                            print("\n╭────────────────────────────────────────────────────────────────────────────────────────╮")
                            print(f"│ {'ID':<12} │ {'Cliente':<25} │ {'Valor Total':<25} │ {'Data':<15} │")
                            print("├──────────────┼───────────────────────────┼───────────────────────────┼─────────────────┤")
                            
                            for venda in vendas:
                                id, cliente_matricula, valor_total, data_venda = venda
                                print(f"│ {id:<12} │ {str(cliente_matricula)[:25]:<25} │ R$ {float(valor_total):<22.2f} │ {data_venda.strftime('%d/%m/%Y'):<15} │")
                            
                            print("╰──────────────┴───────────────────────────┴───────────────────────────┴─────────────────╯")
                            print(f"\nTotal de vendas encontradas: {len(vendas)}")

                            detalhar = input("\nDeseja detalhar alguma venda? (S/N): ").upper()
                            if detalhar == 'S':
                                while True:
                                    venda_id = input("\nDigite o ID da venda a detalhar: ").strip()
                                    if not venda_id.isdigit():
                                        print("\nErro: ID inválido! Deve ser um número.")
                                        continue
                                    detalhar_venda(conn, int(venda_id))
                                    break
                        else:
                            print("\nNenhuma venda encontrada no período especificado.")
                    
                    except Error as e:
                        print(f"\nErro ao consultar vendas: {e}")
                    
                    finally:
                        if cursor:
                            cursor.close()
                    
                    break 
                    
                except ValueError:
                    print("\nErro: Formato de data inválido! Use DD/MM/AAAA.")
                    continue
            return
            
        elif opcao == "3":
            print("\n--- FILTRAR POR CLIENTE ---")
    
            while True:
                nome_cliente = input("Nome do cliente (mínimo 3 caracteres): ").strip()
                
                if len(nome_cliente) < 3:
                    print("\nErro: Por favor, digite pelo menos 3 caracteres para a busca.")
                    continue
                    
                try:
                    cursor = conn.cursor()
                    cursor.execute(""" 
                        SELECT v.id, v.cliente_matricula, v.valor_total, v.data_venda, c.nome
                        FROM vendas v
                        JOIN clientes c ON v.cliente_matricula = c.matricula
                        WHERE c.nome ILIKE %s
                        ORDER BY v.data_venda DESC
                    """, (f"%{nome_cliente}%",))
                    
                    vendas = cursor.fetchall()

                    if vendas:
                        print("\n╭──────────────────────────────────────────────────────────────────────────────────────╮")
                        print(f"│ {'ID':<8} │ {'Cliente':<25} │ {'Matrícula':<12} │ {'Valor Total':<15} │ {'Data':<12} │")
                        print("├──────────┼───────────────────────────┼──────────────┼─────────────────┼──────────────┤")
                        
                        for venda in vendas:
                            id, cliente_matricula, valor_total, data_venda, nome = venda
                            print(f"│ {id:<8} │ {str(nome)[:25]:<25} │ {str(cliente_matricula)[:12]:<12} │ R$ {float(valor_total):<12.2f} │ {data_venda.strftime('%d/%m/%Y'):<12} │")
                        
                        print("╰──────────┴───────────────────────────┴──────────────┴─────────────────┴──────────────╯")
                        print(f"\nTotal de vendas encontradas: {len(vendas)}")

                        detalhar = input("\nDeseja detalhar alguma venda? (S/N): ").upper()
                        if detalhar == 'S':
                            while True:
                                venda_id = input("\nDigite o ID da venda a detalhar: ").strip()
                                if not venda_id.isdigit():
                                    print("\nErro: ID inválido! Deve ser um número.")
                                    continue
                                detalhar_venda(conn, int(venda_id))
                                break
                    else:
                        print("\nNenhuma venda encontrada para o cliente especificado.")
                
                except Error as e:
                    print(f"\nErro ao consultar vendas: {e}")
                
                finally:
                    if cursor:
                        cursor.close()
                
                return            
        elif opcao == "4":
            return
            
        else:
            print("Opção inválida! Digite um número entre 1 e 4.")
            continue
    
def detalhar_venda(conn, venda_id):
    try:
        cursor = conn.cursor()
        
        # Busca dados principais da venda (incluindo desconto)
        cursor.execute("""
            SELECT v.id, c.nome, v.valor_total, v.data_venda, 
                   v.forma_pagamento, v.status, ve.nome as vendedor,
                   v.desconto_aplicado, v.motivo_desconto, v.valor_desconto
            FROM vendas v
            JOIN clientes c ON v.cliente_matricula = c.matricula
            LEFT JOIN vendedor_vendas vv ON v.id = vv.id_venda
            LEFT JOIN vendedores ve ON vv.vendedor_matricula = ve.matricula
            WHERE v.id = %s
        """, (venda_id,))
        venda = cursor.fetchone()
        
        if not venda:
            print("\nVenda não encontrada!")
            return

        # Busca itens da venda
        cursor.execute("""
            SELECT p.id, p.nome, iv.quantidade, iv.valor_unitario,
                   (iv.quantidade * iv.valor_unitario) as subtotal
            FROM itens_venda iv
            JOIN produtos p ON iv.id_produto = p.id
            WHERE iv.id_venda = %s
            ORDER BY p.nome
        """, (venda_id,))
        itens = cursor.fetchall()

        # Cabeçalho
        print("\n" + "=" * 70)
        print(f" DETALHES DA VENDA {venda[0]} ".center(70, "~"))
        print("=" * 70)
        
        # Informações básicas (incluindo status de desconto)
        print(f"\n{'Cliente:':<15} {venda[1]}")
        print(f"{'Vendedor:':<15} {venda[6] or 'Não informado'}")
        print(f"{'Data:':<15} {venda[3].strftime('%d/%m/%Y %H:%M')}")
        print(f"{'Pagamento:':<15} {venda[4]}")
        print(f"{'Status:':<15} {STATUS_VENDA.get(venda[5], venda[5])}")
        if venda[7]:  # desconto_aplicado = TRUE
            print(f"{'Desconto:':<15} {venda[8]}")  # motivo_desconto
        
        # Tabela de itens
        print("\n" + " ITENS ".center(70, "-"))
        print(f"{'Produto':<30} {'Qtd':>5} {'V.Unit.':>10} {'Subtotal':>10}")
        print_linha()
        
        subtotal_calculado = Decimal(0)
        for item in itens:
            subtotal_item = Decimal(item[2]) * Decimal(item[3])
            subtotal_calculado += subtotal_item
            print(
                f"{item[1][:28]:<30} "
                f"{item[2]:>5}x "
                f"R${Decimal(item[3]):>7.2f} "
                f"R${subtotal_item:>8.2f}"
            )
        
        # Totais com desconto (se aplicável)
        print_linha()
        valor_total = Decimal(venda[2])
        
        if venda[7]:  # Se desconto foi aplicado
            print(f"{'SUBTOTAL:':<40} R${subtotal_calculado:>8.2f}")
            print(f"{'DESCONTO:':<40} -R${Decimal(venda[9]):>8.2f}")  # valor_desconto
            print_linha()
            print(f"{'TOTAL FINAL:':<40} R${valor_total:>8.2f}")
        else:
            print(f"{'TOTAL:':<40} R${valor_total:>8.2f}")
        
        print("=" * 70 + "\n")
            
    except Error as e:
        print(f"\nErro ao buscar venda: {e}")
    finally:
        if cursor:
            cursor.close()

def autorizar_venda(conn):
    print("\n--- Autorização de Venda ---")
    
    while True:
        venda_id = input("\nID da venda a autorizar: ").strip()
        if not venda_id.isdigit():
            print("\nID inválido! Deve ser um número.")
            continue
            
        try:
            cursor = conn.cursor()
            
            # Busca a venda e verifica se está pendente
            cursor.execute("""
                SELECT id, status FROM vendas 
                WHERE id = %s
            """, (venda_id,))
            venda = cursor.fetchone()
            
            if not venda:
                print("\nVenda não encontrada!")
                return
                
            if venda[1] != 'PENDENTE':
                print(f"\nEsta venda já está {STATUS_VENDA.get(venda[1], venda[1])}")
                return

            detalhar_venda(conn, venda_id)
            
            # Confirmação
            confirmacao = input("\nConfirmar autorização desta venda? (S/N): ").upper()
            if confirmacao != 'S':
                print("\nOperação cancelada!")
                return
                
            # Atualiza o status da venda
            cursor.execute("""
                UPDATE vendas 
                SET status = 'AUTORIZADA' 
                WHERE id = %s
            """, (venda_id,))
            
            # Registra data de autorização
            cursor.execute("""
                UPDATE vendedor_vendas
                SET data_autorizacao = CURRENT_TIMESTAMP
                WHERE id_venda = %s
            """, (venda_id,))
            
            conn.commit()
            print("\nVenda autorizada com sucesso!")
            return
            
        except Error as e:
            conn.rollback()
            print(f"\nErro ao autorizar venda: {e}")
            return
        finally:
            if cursor:
                cursor.close()

############################################################################################################
# MÉTODOS DE MENU
############################################################################################################

def menu_vendas(conn):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        print("\n=== MENU DE VENDAS ===")
        print("1. Registrar nova venda")
        print("2. Listar vendas")
        print("3. Detalhar venda")
        print("4. Autorizar venda pendente")
        print("5. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            registrar_venda(conn)
            input("\nPressione Enter para continuar...")
        elif opcao == "2":
            os.system('cls' if os.name == 'nt' else 'clear')
            listar_vendas(conn)
            input("\nPressione Enter para continuar...")
        elif opcao == "3":
            while True:
                venda_id = input("\nID da venda a detalhar: ").strip()
                if not venda_id.isdigit():
                    print("\nID inválido! Deve ser um número.")
                    continue
                break
            detalhar_venda(conn, venda_id)
            input("\nPressione Enter para continuar...")
        elif opcao == "4":
            autorizar_venda(conn)
            input("\nPressione Enter para continuar...")
        elif opcao == "5":
            break
        else:
            print("\nOpção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")