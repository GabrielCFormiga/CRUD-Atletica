from psycopg2 import Error

############################################################################################################
# MÉTODOS DE VALIDAÇÃO
############################################################################################################

def validar_nome_produto(nome):
    """
    Valida se o nome do produto é válido.

    Critérios:
    - Deve ter entre 2 e 100 caracteres.
    - Não pode ser composto apenas por espaços.

    Args:
        nome (str): Nome do produto a ser validado.

    Returns:
        bool: True se o nome for válido, False caso contrário.
    """
    return len(nome) >= 2 and len(nome) <= 100 and not nome.isspace()

def validar_quantidade(conn, quantidade):
    """
    Valida se a quantidade é um inteiro positivo.

    Args:
        quantidade (str): Quantidade a ser validada.

    Returns:
        bool: True se a quantidade for válida, False caso contrário.
    """
    try:
        return int(quantidade) >= 0
    except ValueError:
        return False

def validar_preco(preco):
    """
    Valida se o preço é um número positivo.

    Args:
        preco (str): Preço a ser validado.

    Returns:
        bool: True se o preço for válido, False caso contrário.
    """
    try:
        return float(preco) > 0
    except ValueError:
        return False

############################################################################################################
# MÉTODOS DE BUSCA
############################################################################################################

def buscar_produto_por_id(conn, id_produto):
    """
    Busca um produto pelo ID no banco de dados.

    Args:
        id_produto (int): ID do produto a ser buscado.

    Returns:
        tuple or None: Dados do produto se encontrado, ou None se não encontrado ou em caso de erro.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = %s", (id_produto,))
        produto = cursor.fetchone()
        return produto
    except Error as e:
        print(f"Erro ao buscar produto: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

def buscar_produto_por_nome(conn, nome):
    """
    Busca produtos por nome (busca parcial case-insensitive)
    
    Args:
        nome: String com o nome ou parte do nome a buscar
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM produtos 
            WHERE nome ILIKE %s
            ORDER BY nome
        """, (f"%{nome}%",))
        
        produtos = cursor.fetchall()
        
        if produtos:
            print("\n--- Produtos Encontrados ---")
            for produto in produtos:
                print(f"\nID: {produto[0]}")
                print(f"Nome: {produto[1]}")
                print(f"Quantidade: {produto[2]}")
                print(f"Preço: R${produto[3]:.2f}")
            print(f"\nTotal encontrado: {len(produtos)}")
        else:
            print("\nNenhum produto encontrado com esse nome.")
            
    except Error as e:
        print(f"\nErro ao buscar produtos: {e}")
    finally:
        if cursor:
            cursor.close()

############################################################################################################
# MÉTODOS DE CRUD
############################################################################################################

def criar_produto(conn):
    """
    Cadastra um novo produto com validação de dados.

    Fluxo:
    - Solicita nome, quantidade e preço do produto.
    - Valida os dados fornecidos.
    - Insere o produto no banco de dados.

    Returns:
        int or None: ID do produto cadastrado, ou None em caso de erro.
    """
    print("\n--- Cadastro de Produto ---")
    
    # Validação do nome
    while True:
        nome = input("Nome do produto: ").strip()
        if not validar_nome_produto(nome):
            print("Nome inválido! Deve ter entre 2 e 100 caracteres.")
            continue
        
        # Verifica se produto já existe
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM produtos WHERE nome ILIKE %s", (nome,))
            if cursor.fetchone():
                print("Produto com esse nome já cadastrado!")
                continue
        except Error as e:
            print(f"Erro ao verificar produto: {e}")
            return
        finally:
            if cursor:
                cursor.close()
            break

    # Validação da quantidade
    while True:
        quantidade = input("Quantidade em estoque: ").strip()
        if not validar_quantidade(quantidade):
            print("Quantidade inválida! Deve ser um número inteiro positivo.")
            continue
        quantidade = int(quantidade)
        break
    
    # Validação do preço
    while True:
        preco = input("Preço unitário: R$").strip().replace(',', '.')
        if not validar_preco(preco):
            print("Preço inválido! Deve ser um número positivo (use . para decimais).")
            continue
        preco = float(preco)
        break
    
    # Conexão com o banco para inserção
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO produtos (nome, quantidade, preco)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (nome, quantidade, preco))
        produto_id = cursor.fetchone()[0]
        conn.commit()
        
        print("\nProduto cadastrado com sucesso!")
        print(f"ID: {produto_id}")
        print(f"Nome: {nome}")
        print(f"Quantidade: {quantidade}")
        print(f"Preço: R${preco:.2f}")
        
        return produto_id
    except Error as e:
        conn.rollback()
        print(f"\nErro ao cadastrar produto: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

def listar_produtos(conn):
    """
    Lista todos os produtos cadastrados no banco de dados.

    Fluxo:
    - Recupera os dados de todos os produtos.
    - Exibe os dados formatados no console.

    Returns:
        None
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos ORDER BY nome")
        produtos = cursor.fetchall()
        
        print("\n--- Lista de Produtos ---")
        for produto in produtos:
            id, nome, quantidade, preco = produto
            print(f"ID: {id} | Nome: {nome} | Quantidade: {quantidade} | Preço: R${preco:.2f}")
        print(f"Total de produtos: {len(produtos)}")
        
    except Error as e:
        print(f"Erro ao listar produtos: {e}")
    finally:
        if cursor:
            cursor.close()

def atualizar_produto(conn):
    """
    Atualiza os dados de um produto existente.

    Fluxo:
    - Solicita o ID do produto.
    - Exibe os dados atuais do produto.
    - Permite a atualização de nome, quantidade e preço.
    - Atualiza os dados no banco de dados.

    Returns:
        None
    """
    print("\n--- Atualização de Produto ---")
    
    # Busca pelo produto
    while True:
        id_produto = input("Digite o ID do produto: ").strip()
        if not id_produto.isdigit():
            print("ID inválido! Deve ser um número.")
            continue
        
        produto = buscar_produto_por_id(conn, id_produto)
        if not produto:
            print("\nProduto não encontrado!")
            return
        
        break
    
    # Exibe os dados atuais
    print("\nDados atuais do produto:")
    print(f"ID: {produto[0]}")
    print(f"Nome: {produto[1]}")
    print(f"Quantidade: {produto[2]}")
    print(f"Preço: R${produto[3]:.2f}")
    
    # Atualização dos campos
    print("\nDeixe em branco para manter o valor atual")
    
    # Nome
    while True:
        novo_nome = input(f"\nNovo nome [{produto[1]}]: ").strip()
        if not novo_nome:
            novo_nome = produto[1]
            break
        if validar_nome_produto(novo_nome):
            # Verifica se o novo nome já existe (para outro produto)
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM produtos 
                    WHERE nome ILIKE %s AND id != %s
                """, (novo_nome, id_produto))
                if cursor.fetchone():
                    print("Já existe outro produto com esse nome!")
                    continue
            except Error as e:
                print(f"Erro ao verificar produto: {e}")
                return
            finally:
                if cursor:
                    cursor.close()
                break
        print("Nome inválido! Deve ter entre 2 e 100 caracteres.")
    
    # Quantidade
    while True:
        nova_quantidade = input(f"\nNova quantidade [{produto[2]}]: ").strip()
        if not nova_quantidade:
            nova_quantidade = produto[2]
            break
        if validar_quantidade(nova_quantidade):
            nova_quantidade = int(nova_quantidade)
            break
        print("Quantidade inválida! Deve ser um número inteiro positivo.")
    
    # Preço
    while True:
        novo_preco = input(f"\nNovo preço [R${produto[3]:.2f}]: ").strip().replace(',', '.')
        if not novo_preco:
            novo_preco = produto[3]
            break
        if validar_preco(novo_preco):
            novo_preco = float(novo_preco)
            break
        print("Preço inválido! Deve ser um número positivo (use . para decimais).")
    
    # Confirmação
    print("\nDados a serem atualizados:")
    print(f"Nome: {novo_nome}")
    print(f"Quantidade: {nova_quantidade}")
    print(f"Preço: R${novo_preco:.2f}")
    
    confirmacao = input("\nConfirmar atualização? (S/N): ").upper()
    if confirmacao != 'S':
        print("Atualização cancelada!")
        return
    
    # Executa a atualização
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE produtos
            SET nome = %s, quantidade = %s, preco = %s
            WHERE id = %s
        """, (novo_nome, nova_quantidade, novo_preco, id_produto))
        conn.commit()
        print("\nProduto atualizado com sucesso!")
    except Error as e:
        conn.rollback()
        print(f"\nErro ao atualizar produto: {e}")
    finally:
        if cursor:
            cursor.close()

def deletar_produto(conn):
    """
    Remove um produto do sistema com confirmação.

    Fluxo:
    - Solicita o ID do produto.
    - Exibe os dados do produto.
    - Confirma a remoção.
    - Remove o produto do banco de dados.

    Returns:
        None
    """
    print("\n--- Remoção de Produto ---")
    
    # Busca pelo produto
    while True:
        id_produto = input("Digite o ID do produto: ").strip()
        if not id_produto.isdigit():
            print("ID inválido! Deve ser um número.")
            continue
        
        produto = buscar_produto_por_id(conn, id_produto)
        if not produto:
            print("\nProduto não encontrado!")
            return
        
        break
    
    # Exibe os dados do produto
    print("\nDados do produto a ser removido:")
    print(f"ID: {produto[0]}")
    print(f"Nome: {produto[1]}")
    print(f"Quantidade em estoque: {produto[2]}")
    print(f"Preço: R${produto[3]:.2f}")
    
    # Confirmação
    confirmacao = input("\nTem certeza que deseja remover este produto? (S/N): ").upper()
    if confirmacao != 'S':
        print("Remoção cancelada!")
        return
    
    # Verifica se o produto está em alguma venda
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM itens_venda 
            WHERE id_produto = %s LIMIT 1
        """, (id_produto,))
        
        if cursor.fetchone():
            print("\nEste produto está associado a vendas e não pode ser removido!")
            return
    except Error as e:
        print(f"Erro ao verificar vendas: {e}")
        return
    finally:
        if cursor:
            cursor.close()

    # Executa a remoção
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = %s", (id_produto,))
        conn.commit()
        print("\nProduto removido com sucesso!")
    except Error as e:
        conn.rollback()
        print(f"\nErro ao remover produto: {e}")
    finally:
        if cursor:
            cursor.close()

############################################################################################################
# MÉTODOS DE MENU
############################################################################################################

def menu_produtos(conn):
    while True:
        print("\n=== MENU DE PRODUTOS ===")
        print("1. Cadastrar novo produto")
        print("2. Listar todos os produtos")
        print("3. Atualizar produto")
        print("4. Remover produto")
        print("5. Buscar produto por nome")
        print("6. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            criar_produto(conn)
            
        elif opcao == "2":
            listar_produtos(conn)
            
        elif opcao == "3":
            atualizar_produto(conn)
            
        elif opcao == "4":
            deletar_produto(conn)
            
        elif opcao == "5":
            nome = input("\nNome do produto a buscar: ").strip()
            if nome:  # Verifica se não está vazio
                buscar_produto_por_nome(conn, nome)
            else:
                print("Por favor, digite um nome para busca.")
                
        elif opcao == "6":
            break
            
        else:
            print("Opção inválida. Tente novamente.")
