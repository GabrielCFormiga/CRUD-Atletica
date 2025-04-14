from psycopg2 import Error
from decimal import Decimal
from datetime import datetime, timedelta

from clientes import buscar_cliente_por_matricula
from produtos import buscar_produto_por_id, listar_produtos, validar_quantidade
from vendedores import buscar_vendedor_por_matricula

STATUS_VENDA = {
    'PENDENTE': 'Pendente de autorização',
    'AUTORIZADA': 'Autorizada',
    'CANCELADA': 'Cancelada'
}

############################################################################################################
# MÉTODOS DE VALIDAÇÃO
############################################################################################################

def validar_forma_pagamento(forma):
    """
    Valida se a forma de pagamento é válida.

    Critérios:
    - Deve ser 'PIX' ou 'DINHEIRO' (case insensitive).

    Args:
        forma (str): Forma de pagamento a ser validada.

    Returns:
        bool: True se a forma de pagamento for válida, False caso contrário.
    """
    return forma.upper() in ['PIX', 'DINHEIRO']

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
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT tem_desconto_especial(%s);", (matricula,))
        resultado = cursor.fetchone()[0]
        if resultado:
            print("Cliente tem direito ao desconto especial!")
        else:
            print("Cliente não tem direito ao desconto especial.")
        return resultado
    except Exception as e:
        print(f"Erro ao verificar desconto: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
############################################################################################################
# MÉTODOS CRUD
############################################################################################################

def registrar_venda(conn):
    """
    Registra uma nova venda com validação de dados e tratamento correto de tipos numéricos.

    Fluxo:
    - Solicita matrícula do cliente e valida.
    - Solicita forma de pagamento e valida.
    - Permite adicionar itens à venda, validando produto e quantidade.
    - Calcula o total da venda e aplica desconto para sócios.
    - Insere a venda e os itens no banco de dados.

    Returns:
        int or None: ID da venda registrada, ou None em caso de erro ou cancelamento.
    """
    print("\n--- Registro de Nova Venda ---")
    
    # Validação do cliente
    while True:
        matricula = input("Matrícula do cliente: ").strip()
        cliente = buscar_cliente_por_matricula(conn, matricula)
        desconto = verificar_desconto(conn, matricula)
        if not cliente:
            print("Cliente não encontrado!")
            continuar = input("Deseja tentar novamente? (S/N): ").upper()
            if continuar != 'S':
                return None
            continue
        
        print(f"\nCliente: {cliente[1]} ({'Sócio' if cliente[4] else 'Não-sócio'})")
        break
    
    # Validação da forma de pagamento
    while True:
        forma_pagamento = input("\nForma de pagamento (PIX/DINHEIRO): ").strip().upper()
        if not validar_forma_pagamento(forma_pagamento):
            print("Forma de pagamento inválida! Escolha entre PIX ou DINHEIRO.")
            continue
        break
    
    # Seleção do vendedor
    while True:
        matricula_vendedor = input("Matrícula do vendedor: ").strip()
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
            if not validar_quantidade(conn, quantidade):
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
            'preco_unitario': Decimal(str(produto[3]))  # Conversão segura para Decimal
        })
        
        print(f"\nItem adicionado: {produto[1]} - {quantidade}x R${produto[3]:.2f}")
        continuar = input("Deseja adicionar mais itens? (S/N): ").upper()
        if continuar != 'S':
            break
    
    # Cálculo do valor total (usando Decimal para todas operações)
    valor_total = sum(Decimal(item['quantidade']) * item['preco_unitario'] for item in itens)

    # Resumo da venda
    print("\n--- Resumo da Venda ---")
    print(f"Cliente: {cliente[1]}")
    print(f"Forma de pagamento: {forma_pagamento}")
    print("\nItens:")
    for item in itens:
        produto = buscar_produto_por_id(conn, item['id_produto'])
        subtotal = Decimal(item['quantidade']) * item['preco_unitario']
        print(f"- {produto[1]}: {item['quantidade']}x R${item['preco_unitario']:.2f} = R${subtotal:.2f}")
    
    print(f"\nTotal da venda: R${valor_total:.2f}")
    
    # Aplica desconto para sócios (10%) com tratamento correto de tipos
    if cliente[4]:  # Se for sócio
        desconto = valor_total * Decimal('0.10')  # Usando Decimal para o fator de multiplicação
        valor_total -= desconto
        print(f"Desconto (sócio): -R${desconto:.2f}")
        print(f"Total com desconto: R${valor_total:.2f}")
    
    #Aplica desconto se torcer pro Flamengo, a cidade for Sousa ou assistir One Piece
    if(desconto):
        desconto = valor_total * Decimal('0.05')
        valor_total -= desconto
        print(f"Desconto adicional: -R${desconto:.2f}")
        print(f"Total com desconto adicional: R${valor_total:.2f}")

    # Confirmação
    confirmacao = input("\nConfirmar venda? (S/N): ").upper()
    if confirmacao != 'S':
        print("Venda cancelada!")
        return None
    
    # Registra a venda no banco de dados
    try:
        cursor = conn.cursor()
        
        # Insere a venda com status PENDENTE
        cursor.execute("""
            INSERT INTO vendas (cliente_matricula, valor_total, forma_pagamento, status)
            VALUES (%s, %s, %s, 'PENDENTE') RETURNING id
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
        print("\n--- LISTAGEM DE VENDAS ---")
        print("Opções de filtro:")
        print("1. Listar todas as vendas")
        print("2. Filtrar por período")
        print("3. Filtrar por cliente")
        print("4. Voltar ao menu anterior")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            query = """
                SELECT v.id, c.nome, v.valor_total, v.data_venda, v.forma_pagamento, v.status, ve.nome as vendedor
                FROM vendas v
                LEFT JOIN clientes c ON v.cliente_matricula = c.matricula
                LEFT JOIN vendedor_vendas vv ON v.id = vv.id_venda
                LEFT JOIN vendedores ve ON vv.vendedor_matricula = ve.matricula
                ORDER BY v.data_venda DESC
                LIMIT 1000
            """
            params = ()
            break
            
        elif opcao == "2":
            print("\n--- FILTRAR POR PERÍODO ---")
            
            while True:
                try:
                    data_inicio = input("Data inicial (DD/MM/AAAA): ").strip()
                    data_fim = input("Data final (DD/MM/AAAA): ").strip()
                    
                    data_inicio_dt = datetime.strptime(data_inicio, '%d/%m/%Y')
                    data_fim_dt = datetime.strptime(data_fim, '%d/%m/%Y')
                    
                    if data_fim_dt < data_inicio_dt:
                        print("A data final deve ser maior ou igual à data inicial!")
                        continue
                        
                    if (data_fim_dt - data_inicio_dt) > timedelta(days=365):
                        print("Período muito longo! O limite é de 1 ano.")
                        continue
                        
                    query = """
                        SELECT v.id, c.nome, v.valor_total, v.data_venda, v.forma_pagamento, v.status, ve.nome as vendedor
                        FROM vendas v
                        LEFT JOIN clientes c ON v.cliente_matricula = c.matricula
                        LEFT JOIN vendedor_vendas vv ON v.id = vv.id_venda
                        LEFT JOIN vendedores ve ON vv.vendedor_matricula = ve.matricula
                        WHERE v.data_venda BETWEEN %s AND %s
                        ORDER BY v.data_venda DESC
                    """
                    params = (
                        data_inicio_dt.strftime('%Y-%m-%d'),
                        data_fim_dt.strftime('%Y-%m-%d')
                    )
                    break
                    
                except ValueError:
                    print("Formato de data inválido! Use DD/MM/AAAA.")
                    continue
            break
            
        elif opcao == "3":
            print("\n--- FILTRAR POR CLIENTE ---")
            
            while True:
                nome_cliente = input("Nome do cliente (mínimo 3 caracteres): ").strip()
                
                if len(nome_cliente) < 3:
                    print("Por favor, digite pelo menos 3 caracteres para a busca.")
                    continue
                    
                query = """
                    SELECT v.id, c.nome, v.valor_total, v.data_venda, v.forma_pagamento, v.status, ve.nome as vendedor
                    FROM vendas v
                    LEFT JOIN clientes c ON v.cliente_matricula = c.matricula
                    LEFT JOIN vendedor_vendas vv ON v.id = vv.id_venda
                    LEFT JOIN vendedores ve ON vv.vendedor_matricula = ve.matricula
                    WHERE c.nome ILIKE %s
                    ORDER BY v.data_venda DESC
                    LIMIT 200
                """
                params = (f"%{nome_cliente}%",)
                break
            break
            
        elif opcao == "4":
            return
            
        else:
            print("Opção inválida! Digite um número entre 1 e 4.")
            continue
    
    try:    
        cursor = conn.cursor()
        cursor.execute(query, params)
        vendas = cursor.fetchall()
        
        if not vendas:
            print("\nNenhuma venda encontrada com os critérios selecionados.")
            return
            
        print("\n--- RESULTADOS ---")
        print(f"Total de vendas encontradas: {len(vendas)}")
        
        pagina = 0
        itens_por_pagina = 10
        
        while True:
            inicio = pagina * itens_por_pagina
            fim = inicio + itens_por_pagina
            pagina_atual = vendas[inicio:fim]
            
            print(f"\n--- Página {pagina + 1} ---")
            for venda in pagina_atual:
                print("\n" + "-" * 50)
                print(f"ID Venda: {venda[0]}")
                print(f"Cliente: {venda[1]}")
                print(f"Vendedor: {venda[6]}")
                print(f"Valor Total: R${venda[2]:.2f}")
                print(f"Data/Hora: {venda[3].strftime('%d/%m/%Y %H:%M')}")
                print(f"Forma Pagamento: {venda[4]}")
                print(f"Status: {STATUS_VENDA.get(venda[5], venda[5])}")
            
            print("\n" + "-" * 50)
            
            if fim >= len(vendas):
                print("\nFim dos resultados.")
                break
                
            opcao = input("\nPróxima página? (S/N): ").strip().upper()
            if opcao != 'S':
                break
                
            pagina += 1
            
    except Error as e:
        print(f"\nErro ao acessar o banco de dados: {e}")
        
    finally:
        if cursor:
            cursor.close()

def detalhar_venda(conn, venda_id):
    """
    Exibe os detalhes de uma venda específica, incluindo os itens vendidos.

    Fluxo:
    - Busca os dados da venda pelo ID.
    - Exibe informações como cliente, valor total, data e forma de pagamento.
    - Lista os itens da venda, incluindo nome do produto, quantidade, valor unitário e subtotal.

    Args:
        venda_id (int): ID da venda a ser detalhada.

    Returns:
        None
    """
    try:
        cursor = conn.cursor()
        
        # Busca dados da venda
        cursor.execute("""
            SELECT v.id, c.nome, v.valor_total, v.data_venda, v.forma_pagamento
            FROM vendas v
            JOIN clientes c ON v.cliente_matricula = c.matricula
            WHERE v.id = %s
        """, (venda_id,))
        venda = cursor.fetchone()
        
        if venda:
            print(f"\n--- Detalhes da Venda {venda_id} ---")
            print(f"Cliente: {venda[1]}")
            print(f"Valor Total: R${venda[2]:.2f}")
            print(f"Data: {venda[3]}")
            print(f"Forma de Pagamento: {venda[4]}")
            
            # Busca itens da venda
            cursor.execute("""
                SELECT p.nome, iv.quantidade, iv.valor_unitario
                FROM itens_venda iv
                JOIN produtos p ON iv.id_produto = p.id
                WHERE iv.id_venda = %s
            """, (venda_id,))
            itens = cursor.fetchall()
            
            print("\nItens da Venda:")
            for item in itens:
                print(f"- {item[0]} | {item[1]}x R${item[2]:.2f} | Subtotal: R${item[1] * item[2]:.2f}")
        else:
            print("Venda não encontrada!")
            
    except Error as e:
        print(f"Erro ao buscar venda: {e}")
    finally:
        if cursor:
            cursor.close()

def autorizar_venda(conn):
    print("\n--- Autorização de Venda ---")
    
    while True:
        venda_id = input("ID da venda a autorizar: ").strip()
        if not venda_id.isdigit():
            print("ID inválido! Deve ser um número.")
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
                print("Venda não encontrada!")
                continue
                
            if venda[1] != 'PENDENTE':
                print(f"Esta venda já está {STATUS_VENDA.get(venda[1], venda[1])}")
                continue
                
            # Busca o vendedor responsável
            cursor.execute("""
                SELECT v.nome FROM vendedor_vendas vv
                JOIN vendedores v ON vv.vendedor_matricula = v.matricula
                WHERE vv.id_venda = %s
            """, (venda_id,))
            vendedor = cursor.fetchone()
            
            print(f"\nVenda ID: {venda[0]}")
            print(f"Vendedor: {vendedor[0] if vendedor else 'Não informado'}")
            
            confirmacao = input("\nConfirmar autorização desta venda? (S/N): ").upper()
            if confirmacao != 'S':
                print("Operação cancelada!")
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
        print("\n=== MENU DE VENDAS ===")
        print("1. Registrar nova venda")
        print("2. Listar vendas")
        print("3. Detalhar venda")
        print("4. Autorizar venda pendente")
        print("5. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            registrar_venda(conn)
        elif opcao == "2":
            listar_vendas(conn)
        elif opcao == "3":
            venda_id = input("\nID da venda para detalhar: ").strip()
            detalhar_venda(conn, venda_id)
        elif opcao == "4":
            autorizar_venda(conn)
        elif opcao == "5":
            break
        else:
            print("Opção inválida. Tente novamente.")