from psycopg2 import Error

CATEGORIAS = ['Vestuário', 'Acessórios', 'Ingressos', 'Geral']

############################################################################################################
# MÉTODOS DE VALIDAÇÃO
############################################################################################################

def validar_nome_produto(nome):
    """
    Critérios:
    - Deve ter entre 2 e 100 caracteres.
    - Não pode ser composto apenas por espaços.
    """
    return len(nome) >= 2 and len(nome) <= 100 and not nome.isspace()

def validar_quantidade(quantidade):
    """
    Critério:
    - Quantidade é um inteiro positivo.
    """
    try:
        return int(quantidade) >= 0
    except ValueError:
        return False

def validar_preco(preco):
    """
    Critério:
    - Preço é um número positivo.
    """
    try:
        return float(preco) > 0
    except ValueError:
        return False

def validar_cidade(cidade):
    """
    Critérios:
    - Deve conter apenas letras, espaços e hífens
    - Tamanho entre 2 e 50 caracteres
    - Não pode ser composto apenas por espaços
    - Deve ter pelo menos uma letra
    """
    if not cidade or len(cidade.strip()) < 2 or len(cidade) > 50:
        return False
    
    caracteres_permitidos = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ áéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ-")
    return (all(c in caracteres_permitidos for c in cidade) and 
            not cidade.isspace() and
            any(c.isalpha() for c in cidade))

def validar_categoria(categoria):
    categorias_validas = ['Vestuário', 'Acessórios', 'Ingressos', 'Geral']
    return categoria.title() in categorias_validas

############################################################################################################
# MÉTODOS DE BUSCA
############################################################################################################

def buscar_produto_por_id(conn, id_produto):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome, quantidade, preco, cidade, categoria 
            FROM produtos 
            WHERE id = %s
        """, (id_produto,))
        produto = cursor.fetchone()
        if produto:
            return produto
        print("Produto não encontrado!")
        return None
    finally:
        if cursor:
            cursor.close()

def buscar_produto_por_nome(conn, nome):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM produtos 
            WHERE nome ILIKE %s
            ORDER BY nome
        """, (f"%{nome}%",))
        
        produtos = cursor.fetchall()
        
        if produtos:
            print("\n╭──────┬──────────────────────┬──────────┬────────────┬──────────────┬──────────────╮")
            print(f"│ {'ID':<4} │ {'Nome':<20} │ {'Estoque':<8} │ {'Preço':<10} │ {'Cidade':<12} │ {'Categoria':<12} │")
            print("├──────┼──────────────────────┼──────────┼────────────┼──────────────┼──────────────┤")
            for produto in produtos:
                print(f"│ {produto[0]:<4} │ {produto[1][:20]:<20} │ {produto[2]:<8} │ R${produto[3]:<8.2f} │ {produto[4][:12]:<12} │ {produto[5][:12]:<12} │")
            print("╰──────┴──────────────────────┴──────────┴────────────┴──────────────┴──────────────╯")
            print(f"\nTotal encontrado: {len(produtos)} produto(s)")
        else:
            print("\nNenhum produto encontrado com esse nome.")
            
    except Error as e:
        print(f"\nErro ao buscar produtos: {e}")
    finally:
        if cursor:
            cursor.close()

def buscar_produtos_filtrados(conn):
    """
    Busca produtos com filtros avançados:
    - Nome (parcial)
    - Faixa de preço
    - Categoria
    - Cidade de fabricação (Mari)
    """
    print("\n--- Busca Avançada de Produtos ---")
    
    filtros = {}
    params = []
    
    # Filtro por nome
    nome = input("Nome do produto (deixe em branco para ignorar): ").strip()
    if nome:
        filtros["nome"] = "nome ILIKE %s"
        params.append(f"%{nome}%")
    
    # Filtro por faixa de preço
    print("\nFaixa de preço:")
    try:
        preco_min = input("Preço mínimo (deixe em branco para ignorar): ").strip()
        if preco_min:
            filtros["preco_min"] = "preco >= %s"
            params.append(float(preco_min))
        
        preco_max = input("Preço máximo (deixe em branco para ignorar): ").strip()
        if preco_max:
            filtros["preco_max"] = "preco <= %s"
            params.append(float(preco_max))
    except ValueError:
        print("Valor inválido para preço! Use números decimais.")
        return
    
    # Filtro por categoria
    print("\nCategorias disponíveis:")
    for i, cat in enumerate(CATEGORIAS, 1):
        print(f"{i}. {cat}")
    
    categoria = input("\nNúmero da categoria (deixe em branco para todas): ").strip()
    if categoria:
        try:
            opcao = int(categoria)
            if 1 <= opcao <= len(CATEGORIAS):
                filtros["categoria"] = "categoria = %s"
                params.append(CATEGORIAS[opcao-1])
            else:
                print("Número de categoria inválido!")
        except ValueError:
            print("Digite apenas números para categoria!")
            return
    
    # Filtro por cidade (Mari)
    filtro_mari = input("\nIncluir apenas produtos fabricados em Mari? (S/N): ").upper().strip()
    if filtro_mari == 'S':
        filtros["cidade"] = "cidade ILIKE %s"
        params.append("Mari")
    
    # Construção da query
    query = "SELECT * FROM produtos"
    if filtros:
        query += " WHERE " + " AND ".join(filtros.values())
    query += " ORDER BY nome"
    
    # Execução da busca
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        produtos = cursor.fetchall()
        
        if produtos:
            print("\n╭──────┬──────────────────────┬──────────┬────────────┬──────────────┬──────────────╮")
            print(f"│ {'ID':<4} │ {'Nome':<20} │ {'Estoque':<8} │ {'Preço':<10} │ {'Cidade':<12} │ {'Categoria':<12} │")
            print("├──────┼──────────────────────┼──────────┼────────────┼──────────────┼──────────────┤")
            for produto in produtos:
                print(f"│ {produto[0]:<4} │ {produto[1][:20]:<20} │ {produto[2]:<8} │ R${produto[3]:<8.2f} │ {produto[4][:12]:<12} │ {produto[5][:12]:<12} │")
            print("╰──────┴──────────────────────┴──────────┴────────────┴──────────────┴──────────────╯")
            print(f"\nTotal encontrado: {len(produtos)} produto(s)")
        else:
            print("\nNenhum produto encontrado com os filtros selecionados.")
            
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
    Fluxo:
    - Solicita nome, quantidade e preço do produto.
    - Valida os dados fornecidos.
    - Insere o produto no banco de dados.
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

    # Cidade
    while True:
        cidade = input("Cidade onde foi fabricado: ").strip()
        cidade = cidade.title().strip()
        if not validar_cidade(cidade):
            print("Cidade inválida! Deve conter 2 a 50 caracteres (apenas letras, espaços e hífens).")
            continue
        break

    # Validação de categoria
    while True:
        print("\nCategorias disponíveis:")
        for i, cat in enumerate(CATEGORIAS, 1):
            print(f"{i}. {cat}")
        
        try:
            opcao = int(input("Escolha o número da categoria: "))
            if 1 <= opcao <= len(CATEGORIAS):
                categoria = CATEGORIAS[opcao-1]
                break
        except ValueError:
            pass
        print("Opção inválida! Escolha um número da lista.")
    
    # Conexão com o banco para inserção
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO produtos (nome, quantidade, preco, cidade, categoria)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        cursor.execute(query, (nome, quantidade, preco, cidade, categoria))
        
        produto_id = cursor.fetchone()[0]
        conn.commit()
        
        print("\nProduto cadastrado com sucesso!")
        print(f"ID: {produto_id}")
        print(f"Nome: {nome}")
        print(f"Quantidade: {quantidade}")
        print(f"Preço: R${preco:.2f}")
        print(f"Cidade: {cidade}")
        print(f"Categoria: {categoria}")
        
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
    Fluxo:
    - Recupera os dados de todos os produtos.
    - Exibe os dados formatados no console.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos ORDER BY nome")
        produtos = cursor.fetchall()
        
        print("\n╭──────┬──────────────────────┬──────────┬────────────┬──────────────┬──────────────╮")
        print(f"│ {'ID':<4} │ {'Nome':<20} │ {'Estoque':<8} │ {'Preço':<10} │ {'Cidade':<12} │ {'Categoria':<12} │")
        print("├──────┼──────────────────────┼──────────┼────────────┼──────────────┼──────────────┤")
        for produto in produtos:
            print(f"│ {produto[0]:<4} │ {produto[1][:20]:<20} │ {produto[2]:<8} │ R${produto[3]:<8.2f} │ {produto[4][:12]:<12} │ {produto[5][:12]:<12} │")
        print("╰──────┴──────────────────────┴──────────┴────────────┴──────────────┴──────────────╯")
        print(f"Total de produtos cadastrados: {len(produtos)}")
        
    except Error as e:
        print(f"Erro ao listar produtos: {e}")
    finally:
        if cursor:
            cursor.close()

def atualizar_produto(conn):
    """
    Fluxo:
    - Solicita o ID do produto.
    - Exibe os dados atuais do produto.
    - Permite a atualização de nome, quantidade e preço.
    - Atualiza os dados no banco de dados.
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
    print(f"Cidade: {produto[4]}")
    print(f"Categoria: {produto[5]}")
    
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

    # Cidade
    while True:
        nova_cidade = input(f"\nNova cidade [{produto[4]}]: ").strip()
        if not nova_cidade:
            nova_cidade = produto[4]
            break
        nova_cidade = nova_cidade.title().strip()
        if validar_cidade(nova_cidade):
            break
        print("Cidade inválida! Deve conter 2 a 50 caracteres (apenas letras, espaços e hífens).")
    
    # Categoria
    print(f"\nCategoria atual: {produto[5]}") 
    print("Categorias disponíveis:")
    for i, cat in enumerate(CATEGORIAS, 1):
        print(f"{i}. {cat}")

    while True:
        nova_categoria = input("\nNúmero da nova categoria (ou Enter para manter): ").strip()
        if not nova_categoria:
            nova_categoria = produto[5]
            break
        try:
            opcao = int(nova_categoria)
            if 1 <= opcao <= len(CATEGORIAS):
                nova_categoria = CATEGORIAS[opcao-1]
                break
            print(f"Opção inválida! Digite um número entre 1 e {len(CATEGORIAS)}.")
        except ValueError:
            print("Entrada inválida! Digite apenas números.")

    # Confirmação
    print("\nDados a serem atualizados:")
    print(f"Nome: {novo_nome}")
    print(f"Quantidade: {nova_quantidade}")
    print(f"Preço: R${novo_preco:.2f}")
    print(f"Cidade: {nova_cidade}")
    print(f"Categoria: {nova_categoria}")
    
    confirmacao = input("\nConfirmar atualização? (S/N): ").upper()
    if confirmacao != 'S':
        print("Atualização cancelada!")
        return
    
    # Executa a atualização
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE produtos
            SET nome = %s, quantidade = %s, preco = %s, cidade = %s, categoria = %s
            WHERE id = %s
        """, (novo_nome, nova_quantidade, novo_preco, nova_cidade, nova_categoria, id_produto))
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
        print("6. Busca avançada de produtos")
        print("7. Voltar ao menu principal")
        
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
            if nome:
                buscar_produto_por_nome(conn, nome)
            else:
                print("Por favor, digite um nome para busca.")
        elif opcao == "6":
            buscar_produtos_filtrados(conn)
        elif opcao == "7":
            break
        else:
            print("Opção inválida. Tente novamente.")
