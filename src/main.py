from database import conecta, desconecta
from psycopg2 import Error
from datetime import datetime, timedelta
from decimal import Decimal

############################################################################################################
# MÉTODOS DE VALIDAÇÃO DE CLIENTES
############################################################################################################

def validar_matricula(matricula):
    """
    Valida se a matrícula é válida.
    
    Critérios:
    - Contém apenas dígitos.
    - Tamanho entre 6 e 20 caracteres.
    
    Args:
        matricula (str): Número de matrícula a ser validado.
    
    Returns:
        bool: True se a matrícula for válida, False caso contrário.
    """
    return matricula.isdigit() and 6 <= len(matricula) <= 20


def validar_nome(nome):
    """
    Valida se o nome é válido.
    
    Critérios:
    - Contém apenas letras e espaços.
    - Tamanho mínimo de 3 caracteres.
    
    Args:
        nome (str): Nome a ser validado.
    
    Returns:
        bool: True se o nome for válido, False caso contrário.
    """
    return all(c.isalpha() or c.isspace() for c in nome) and len(nome) >= 3


def validar_email(email):
    """
    Valida se o email é válido.
    
    Critérios:
    - Contém o caractere '@'.
    - Contém um '.' após o '@'.
    - Tamanho mínimo de 5 caracteres.
    
    Args:
        email (str): Email a ser validado.
    
    Returns:
        bool: True se o email for válido, False caso contrário.
    """
    return '@' in email and '.' in email.split('@')[-1] and len(email) >= 5


def validar_telefone(telefone):
    """
    Valida se o telefone é válido.
    
    Critérios:
    - Aceita apenas números no formato (XX) XXXXX-XXXX ou similar.
    - Tamanho entre 10 e 11 dígitos após remover caracteres não numéricos.
    
    Args:
        telefone (str): Telefone a ser validado.
    
    Returns:
        bool: True se o telefone for válido, False caso contrário.
    """
    telefone = ''.join(filter(str.isdigit, telefone))
    return 10 <= len(telefone) <= 11


############################################################################################################
# MÉTODOS DE BUSCA DE CLIENTES
############################################################################################################

def buscar_cliente_por_matricula(matricula):
    """
    Busca um cliente pelo número de matrícula no banco de dados.
    
    Args:
        matricula (str): Número de matrícula do cliente.
    
    Returns:
        tuple or None: Dados do cliente se encontrado, ou None se não encontrado ou em caso de erro.
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE matricula = %s", (matricula,))
        cliente = cursor.fetchone()
        return cliente
    except Error as e:
        print(f"Erro ao buscar cliente: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

############################################################################################################
# MÉTODOS CRUD DE CLIENTES
############################################################################################################

def criar_cliente():
    """
    Cadastra um novo cliente com validação de dados.
    
    Fluxo:
    - Solicita matrícula, nome, email, telefone e status de sócio.
    - Valida os dados fornecidos.
    - Insere o cliente no banco de dados.
    
    Returns:
        None
    """
    print("\n--- Cadastro de Cliente ---")
    
    # Validação da matrícula
    while True:
        matricula = input("Matrícula: ").strip()
        if not validar_matricula(matricula):
            print("Matrícula inválida! Deve conter apenas números (6-20 dígitos).")
            continue
        
        if buscar_cliente_por_matricula(matricula):
            print("Matrícula já cadastrada no sistema!")
            return
        break
    
    # Validação do nome
    while True:
        nome = input("Nome completo: ").strip()
        if not validar_nome(nome):
            print("Nome inválido! Deve conter apenas letras e espaços (mínimo 3 caracteres).")
            continue
        break
    
    # Validação do email
    while True:
        email = input("Email: ").strip()
        if not validar_email(email):
            print("Email inválido! Deve estar no formato 'exemplo@dominio.com'.")
            continue
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM clientes WHERE email = %s", (email,))
            if cursor.fetchone():
                print("Email já cadastrado no sistema!")
                continue
        except Error as e:
            print(f"Erro ao verificar email: {e}")
            return
        finally:
            if cursor:
                cursor.close()
            break
    
    # Validação do telefone
    while True:
        telefone = input("Telefone (com DDD): ").strip()
        if not validar_telefone(telefone):
            print("Telefone inválido! Use o formato (XX) XXXXX-XXXX ou similar.")
            continue
        break
    
    # Validação do status de sócio
    while True:
        eh_socio = input("É sócio? (S/N): ").upper()
        if eh_socio not in ('S', 'N'):
            print("Opção inválida! Digite S para Sim ou N para Não.")
            continue
        break
    
    # Formata os dados antes de inserir
    telefone = ''.join(filter(str.isdigit, telefone))
    eh_socio = eh_socio == 'S'
    
    # Conexão com o banco para inserção    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clientes (matricula, nome, email, telefone, eh_socio)
            VALUES (%s, %s, %s, %s, %s)
        """, (matricula, nome, email, telefone, eh_socio))
        conn.commit()
        print("\nCliente cadastrado com sucesso!")
        print(f"Matrícula: {matricula}")
        print(f"Nome: {nome}")
        print(f"Email: {email}")
        print(f"Telefone: {telefone}")
        print(f"Status: {'Sócio' if eh_socio else 'Não-sócio'}")
    except Error as e:
        conn.rollback()
        print(f"\nErro ao cadastrar cliente: {e}")
    finally:
        if cursor:
            cursor.close()

def listar_clientes():
    """
    Lista todos os clientes cadastrados no banco de dados.
    
    Fluxo:
    - Recupera os dados de todos os clientes.
    - Exibe os dados formatados no console.
    
    Returns:
        None
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes ORDER BY nome")
        clientes = cursor.fetchall()
        
        print("\n--- Lista de Clientes ---")
        for cliente in clientes:
            matricula, nome, email, telefone, eh_socio = cliente
            status = "Sócio" if eh_socio else "Não-sócio"
            print(f"Matrícula: {matricula} | Nome: {nome} | Email: {email} | Tel: {telefone} | Status: {status}")
        print(f"Total de clientes: {len(clientes)}")
        
    except Error as e:
        print(f"Erro ao listar clientes: {e}")
    finally:
        if cursor:
            cursor.close()


def atualizar_cliente():
    """
    Atualiza os dados de um cliente existente.
    
    Fluxo:
    - Solicita a matrícula do cliente.
    - Exibe os dados atuais do cliente.
    - Permite a atualização de nome, email, telefone e status de sócio.
    - Atualiza os dados no banco de dados.
    
    Returns:
        None
    """
    print("\n--- Atualização de Cliente ---")
    
    # Busca pelo cliente
    matricula = input("Digite a matrícula do cliente: ").strip()
    cliente = buscar_cliente_por_matricula(matricula)
    
    if not cliente:
        print("\nCliente não encontrado!")
        return
    
    # Exibe os dados atuais
    print("\nDados atuais do cliente:")
    print(f"Matrícula: {cliente[0]}")
    print(f"Nome: {cliente[1]}")
    print(f"Email: {cliente[2]}")
    print(f"Telefone: {cliente[3]}")
    print(f"Status: {'Sócio' if cliente[4] else 'Não-sócio'}")
    
    # Atualização dos campos
    print("\nDeixe em branco para manter o valor atual")
    
    # Nome
    while True:
        novo_nome = input(f"\nNovo nome [{cliente[1]}]: ").strip()
        if not novo_nome:
            novo_nome = cliente[1]
            break
        if validar_nome(novo_nome):
            break
        print("Nome inválido! Deve conter apenas letras e espaços (mínimo 3 caracteres).")
    
    # Email
    while True:
        novo_email = input(f"\nNovo email [{cliente[2]}]: ").strip()
        if not novo_email:
            novo_email = cliente[2]
            break
        if validar_email(novo_email):
            if novo_email != cliente[2]:  # Só verifica se mudou
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1 FROM clientes WHERE email = %s AND matricula != %s", 
                                    (novo_email, matricula))
                    if cursor.fetchone():
                        print("Email já está em uso por outro cliente!")
                        continue
                except Error as e:
                    print(f"Erro ao verificar email: {e}")
                    return
                finally:
                    if cursor:
                        cursor.close()
            break
        print("Email inválido! Deve estar no formato 'exemplo@dominio.com'.")
    
    # Telefone
    while True:
        novo_telefone = input(f"\nNovo telefone [{cliente[3]}]: ").strip()
        if not novo_telefone:
            novo_telefone = cliente[3]
            break
        if validar_telefone(novo_telefone):
            novo_telefone = ''.join(filter(str.isdigit, novo_telefone))
            break
        print("Telefone inválido! Use o formato (XX) XXXXX-XXXX ou similar.")
    
    # Status de sócio
    while True:
        novo_status = input(f"\nÉ sócio? [{'S' if cliente[4] else 'N'}] (S/N): ").upper().strip()
        if not novo_status:
            novo_status = 'S' if cliente[4] else 'N'
            break
        if novo_status in ('S', 'N'):
            break
        print("Opção inválida! Digite S para Sim ou N para Não.")
    
    # Confirmação
    print("\nDados a serem atualizados:")
    print(f"Nome: {novo_nome}")
    print(f"Email: {novo_email}")
    print(f"Telefone: {novo_telefone}")
    print(f"Status: {'Sócio' if novo_status == 'S' else 'Não-sócio'}")
    
    confirmacao = input("\nConfirmar atualização? (S/N): ").upper()
    if confirmacao != 'S':
        print("Atualização cancelada!")
        return
    
    # Executa a atualização
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clientes
            SET nome = %s, email = %s, telefone = %s, eh_socio = %s
            WHERE matricula = %s
        """, (novo_nome, novo_email, novo_telefone, novo_status == 'S', matricula))
        conn.commit()
        print("\nCliente atualizado com sucesso!")
    except Error as e:
        conn.rollback()
        print(f"\nErro ao atualizar cliente: {e}")
    finally:
        if cursor:
            cursor.close()


def deletar_cliente(matricula):
    """
    Remove um cliente do banco de dados.
    
    Args:
        matricula (str): Matrícula do cliente a ser removido.
    
    Returns:
        None
    """
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE matricula = %s", (matricula,))
        conn.commit()
        print("Cliente deletado com sucesso!")
    except Error as e:
        print(f"Erro ao deletar cliente: {e}")
    finally:
        if cursor:
            cursor.close()


def buscar_cliente_por_nome(nome):
    """
    Busca clientes pelo nome no banco de dados.
    
    Args:
        nome (str): Nome ou parte do nome do cliente a ser buscado.
    
    Returns:
        None
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE nome ILIKE %s ORDER BY nome", (f"%{nome}%",))
        clientes = cursor.fetchall()
        
        if clientes:
            print("\n--- Resultados da Busca ---")
            for cliente in clientes:
                matricula, nome, email, telefone, eh_socio = cliente
                status = "Sócio" if eh_socio else "Não-sócio"
                print(f"Matrícula: {matricula} | Nome: {nome} | Email: {email} | Tel: {telefone} | Status: {status}")
        else:
            print("Nenhum cliente encontrado com esse nome.")
            
    except Error as e:
        print(f"Erro ao buscar cliente: {e}")
    finally:
        if cursor:
            cursor.close()

############################################################################################################
# MÉTODOS DE VALIDAÇÃO DE PRODUTOS
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


def validar_quantidade(quantidade):
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
# MÉTODOS DE BUSCA DE PRODUTOS
############################################################################################################

def buscar_produto_por_id(id_produto):
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

def buscar_produto_por_nome(nome):
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
# MÉTODOS CRUD DE PRODUTOS
############################################################################################################

def criar_produto():
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


def listar_produtos():
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


def atualizar_produto():
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
        
        produto = buscar_produto_por_id(id_produto)
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


def deletar_produto():
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
        
        produto = buscar_produto_por_id(id_produto)
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
# MÉTODOS DE VALIDAÇÃO DE VENDAS
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


def buscar_venda_por_id(venda_id):
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


def verificar_estoque_suficiente(id_produto, quantidade):
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

############################################################################################################
# MÉTODOS CRUD DE VENDAS
############################################################################################################

def registrar_venda():
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
        cliente = buscar_cliente_por_matricula(matricula)
        
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
    
    # Cadastro dos itens da venda
    itens = []
    while True:
        print("\n--- Adicionar Item à Venda ---")
        listar_produtos()
        
        # Validação do produto
        while True:
            id_produto = input("\nID do produto (ou 0 para finalizar): ").strip()
            if id_produto == "0":
                break
            
            if not id_produto.isdigit():
                print("ID inválido! Deve ser um número.")
                continue
            
            produto = buscar_produto_por_id(id_produto)
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
            if not verificar_estoque_suficiente(id_produto, quantidade):
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
        produto = buscar_produto_por_id(item['id_produto'])
        subtotal = Decimal(item['quantidade']) * item['preco_unitario']
        print(f"- {produto[1]}: {item['quantidade']}x R${item['preco_unitario']:.2f} = R${subtotal:.2f}")
    
    print(f"\nTotal da venda: R${valor_total:.2f}")
    
    # Aplica desconto para sócios (10%) com tratamento correto de tipos
    if cliente[4]:  # Se for sócio
        desconto = valor_total * Decimal('0.10')  # Usando Decimal para o fator de multiplicação
        valor_total -= desconto
        print(f"Desconto (sócio): -R${desconto:.2f}")
        print(f"Total com desconto: R${valor_total:.2f}")
    
    # Confirmação
    confirmacao = input("\nConfirmar venda? (S/N): ").upper()
    if confirmacao != 'S':
        print("Venda cancelada!")
        return None
    
    # Registra a venda no banco de dados
    try:
        cursor = conn.cursor()
        
        # Insere a venda (convertendo para float para o PostgreSQL)
        cursor.execute("""
            INSERT INTO vendas (cliente_matricula, valor_total, forma_pagamento)
            VALUES (%s, %s, %s) RETURNING id
        """, (matricula, float(valor_total), forma_pagamento))
        venda_id = cursor.fetchone()[0]
        
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
        return venda_id
        
    except Error as e:
        conn.rollback()
        print(f"\nErro ao registrar venda: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

def listar_vendas():
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
                SELECT v.id, c.nome, v.valor_total, v.data_venda, v.forma_pagamento
                FROM vendas v
                JOIN clientes c ON v.cliente_matricula = c.matricula
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
                        SELECT v.id, c.nome, v.valor_total, v.data_venda, v.forma_pagamento
                        FROM vendas v
                        JOIN clientes c ON v.cliente_matricula = c.matricula
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
                    SELECT v.id, c.nome, v.valor_total, v.data_venda, v.forma_pagamento
                    FROM vendas v
                    JOIN clientes c ON v.cliente_matricula = c.matricula
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
                print(f"Valor Total: R${venda[2]:.2f}")
                print(f"Data/Hora: {venda[3].strftime('%d/%m/%Y %H:%M')}")
                print(f"Forma Pagamento: {venda[4]}")
            
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

def detalhar_venda(venda_id):
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

############################################################################################################
# MÉTODOS CRUD DE RELATÓRIOS
############################################################################################################

def relatorio_socios():
    """
    Gera relatório estatístico sobre sócios com tratamento de erros robusto.
    
    Fluxo:
    1. Conecta ao banco de dados
    2. Executa query para obter estatísticas
    3. Formata e exibe resultados
    4. Trata possíveis erros
    """
    try:
        cursor = conn.cursor()
        
        # Query com tratamento de valores nulos
        cursor.execute("""
            SELECT 
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN eh_socio = TRUE THEN 1 ELSE 0 END), 0) AS socios,
                COALESCE(SUM(CASE WHEN eh_socio = FALSE THEN 1 ELSE 0 END), 0) AS nao_socios,
                ROUND(
                    COALESCE(SUM(CASE WHEN eh_socio = TRUE THEN 1 ELSE 0 END), 0) * 100.0 / 
                    NULLIF(COUNT(*), 0), 
                2
                ) AS percentual_socios
            FROM clientes
        """)
        
        resultado = cursor.fetchone()
        
        # Validação dos resultados
        if not resultado or len(resultado) < 4:
            print("\nErro: Dados do relatório inconsistentes")
            return
        
        # Formatação do relatório
        print("\n=== RELATÓRIO DE SÓCIOS ===")
        print(f"\nTotal de clientes cadastrados: {resultado[0]}")
        print(f"Quantidade de sócios: {resultado[1]}")
        print(f"Quantidade de não-sócios: {resultado[2]}")
        print(f"\nPercentual de sócios: {resultado[3]}%")
        
        # Análise adicional
        if resultado[0] > 0:
            if resultado[1] == 0:
                print("\nALERTA: Nenhum sócio cadastrado!")
            elif resultado[2] == 0:
                print("\nINFO: Todos os clientes são sócios!")
        
    except Error as e:
        print(f"\nErro ao gerar relatório: {str(e)}")
    finally:
        if cursor:
            cursor.close()

def relatorio_estoque_baixo(limite=5):
    """
    Gera relatório de produtos com estoque baixo com validações.
    
    Parâmetros:
        limite (int): Quantidade mínima para considerar estoque baixo (padrão=5)
    
    Fluxo:
    1. Valida parâmetro de limite
    2. Conecta ao banco
    3. Executa query com filtro
    4. Exibe resultados formatados
    """
    # Validação do parâmetro
    try:
        limite = int(limite)
        if limite < 1:
            print("\nErro: O limite deve ser um número positivo")
            return
    except ValueError:
        print("\nErro: O limite deve ser um número inteiro")
        return
    
    try:
        cursor = conn.cursor()
        
        # Query com ordenação por prioridade (estoque mais baixo primeiro)
        cursor.execute("""
            SELECT p.id, p.nome, p.quantidade, p.preco,
                   ROUND(p.preco * p.quantidade, 2) AS valor_total_estoque
            FROM produtos p
            WHERE p.quantidade < %s
            ORDER BY p.quantidade ASC, p.nome ASC
        """, (limite,))
        
        produtos = cursor.fetchall()
        
        # Cabeçalho do relatório
        print(f"\n=== RELATÓRIO DE ESTOQUE BAIXO (< {limite} unidades) ===")
        
        if not produtos:
            print("\nNenhum produto com estoque abaixo do limite.")
            return
        
        # Dados estatísticos
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_produtos,
                SUM(quantidade) AS total_unidades,
                ROUND(AVG(quantidade), 2) AS media_estoque,
                MIN(quantidade) AS menor_estoque
            FROM produtos
            WHERE quantidade < %s
        """, (limite,))
        
        stats = cursor.fetchone()
        
        # Exibe estatísticas
        print(f"\nTotal de produtos: {stats[0]}")
        print(f"Total de unidades em estoque: {stats[1]}")
        print(f"Média de estoque: {stats[2]} unidades")
        print(f"Menor estoque: {stats[3]} unidades")
        
        # Tabela de produtos
        print("\nDetalhamento por produto:")
        print("\n" + "=" * 80)
        print(f"{'ID':<5} | {'Nome':<30} | {'Estoque':<10} | {'Preço Unit.':<12} | {'Valor Total':<12}")
        print("-" * 80)
        
        for produto in produtos:
            alerta = "(!)" if produto[2] < 2 else ""  # Alerta para estoque muito baixo
            print(f"{produto[0]:<5} | {produto[1][:30]:<30} | {produto[2]:<10}{alerta} | R$ {produto[3]:<10.2f} | R$ {produto[4]:<10.2f}")
        
        print("=" * 80)
        print("(!) - Estoque muito baixo (menos de 2 unidades)")
        
    except Error as e:
        print(f"\nErro ao gerar relatório: {str(e)}")
    finally:
        if cursor:
            cursor.close()

############################################################################################################
# MÉTODOS DE MENU
############################################################################################################

def menu_clientes():
    while True:
        print("\n=== MENU DE CLIENTES ===")
        print("1. Cadastrar novo cliente")
        print("2. Listar todos os clientes")
        print("3. Atualizar cliente")
        print("4. Remover cliente")
        print("5. Buscar cliente por nome")
        print("6. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            criar_cliente()
            
        elif opcao == "2":
            listar_clientes()
            
        elif opcao == "3":
            atualizar_cliente()
            
        elif opcao == "4":
            matricula = input("\nMatrícula do cliente a ser removido: ")
            cliente = buscar_cliente_por_matricula(matricula)
            
            if cliente:
                confirmacao = input(f"Tem certeza que deseja remover {cliente[1]} (matrícula: {matricula})? (S/N): ").upper()
                if confirmacao == "S":
                    deletar_cliente(matricula)
            else:
                print("Cliente não encontrado!")
                
        elif opcao == "5":
            nome = input("\nNome do cliente a buscar: ")
            buscar_cliente_por_nome(nome)
            
        elif opcao == "6":
            break
            
        else:
            print("Opção inválida. Tente novamente.")

def menu_produtos():
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
            criar_produto()
            
        elif opcao == "2":
            listar_produtos()
            
        elif opcao == "3":
            atualizar_produto()
            
        elif opcao == "4":
            deletar_produto()
            
        elif opcao == "5":
            nome = input("\nNome do produto a buscar: ").strip()
            if nome:  # Verifica se não está vazio
                buscar_produto_por_nome(nome)
            else:
                print("Por favor, digite um nome para busca.")
                
        elif opcao == "6":
            break
            
        else:
            print("Opção inválida. Tente novamente.")

def menu_vendas():
    while True:
        print("\n=== MENU DE VENDAS ===")
        print("1. Registrar nova venda")
        print("2. Listar vendas")
        print("3. Detalhar venda")
        print("4. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            registrar_venda()
            
        elif opcao == "2":
            listar_vendas()
            
        elif opcao == "3":
            while True:
                venda_id = input("\nID da venda para detalhar: ").strip()
                if not venda_id.isdigit():
                    print("ID inválido! Deve ser um número.")
                    continue
                
                detalhar_venda(venda_id)
                break
            
        elif opcao == "4":
            break
            
        else:
            print("Opção inválida. Tente novamente.")

def menu_relatorios():
    """
    Menu de relatórios com opções validadas.
    """
    while True:
        print("\n=== MENU DE RELATÓRIOS ===")
        print("1. Relatório de sócios")
        print("2. Relatório de estoque baixo")
        print("3. Configurar limite para estoque baixo")
        print("4. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            relatorio_socios()
            
        elif opcao == "2":
            relatorio_estoque_baixo()
            
        elif opcao == "3":
            while True:
                try:
                    novo_limite = input("\nNovo limite para estoque baixo (padrão=5): ").strip()
                    if not novo_limite:
                        print("Mantendo o valor padrão (5).")
                        break
                    
                    novo_limite = int(novo_limite)
                    if novo_limite < 1:
                        print("O limite deve ser pelo menos 1.")
                        continue
                    
                    print(f"\nConfigurando novo limite para {novo_limite} unidades.")
                    relatorio_estoque_baixo(novo_limite)
                    break
                    
                except ValueError:
                    print("Por favor, digite um número inteiro válido.")
            
        elif opcao == "4":
            break
            
        else:
            print("Opção inválida. Digite um número entre 1 e 4.")

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
                menu_vendas()
            elif opcao == "4":
                menu_relatorios()
            elif opcao == "5":
                print("Saindo do sistema...")
                desconecta(conn)
                break
            else:
                print("Opção inválida. Tente novamente.")
    return None

if __name__ == "__main__":
    main()