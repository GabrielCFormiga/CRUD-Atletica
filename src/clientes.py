from psycopg2 import Error

############################################################################################################
# MÉTODOS DE VALIDAÇÃO
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
# MÉTODOS DE BUSCA
############################################################################################################

def buscar_cliente_por_matricula(conn, matricula):
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

def buscar_cliente_por_nome(conn, nome):
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
# MÉTODOS DE CRUD
############################################################################################################

def criar_cliente(conn):
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
        
        if buscar_cliente_por_matricula(conn, matricula):
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

def listar_clientes(conn):
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

def atualizar_cliente(conn):
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
    cliente = buscar_cliente_por_matricula(conn, matricula)
    
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

def deletar_cliente(conn, matricula):
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

############################################################################################################
# MÉTODOS DE MENU
############################################################################################################

def menu_clientes(conn):
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
            criar_cliente(conn)
            
        elif opcao == "2":
            listar_clientes(conn)
            
        elif opcao == "3":
            atualizar_cliente(conn)
            
        elif opcao == "4":
            matricula = input("\nMatrícula do cliente a ser removido: ")
            cliente = buscar_cliente_por_matricula(conn, matricula)
            
            if cliente:
                confirmacao = input(f"Tem certeza que deseja remover {cliente[1]} (matrícula: {matricula})? (S/N): ").upper()
                if confirmacao == "S":
                    deletar_cliente(conn, matricula)
            else:
                print("Cliente não encontrado!")
                
        elif opcao == "5":
            nome = input("\nNome do cliente a buscar: ")
            buscar_cliente_por_nome(conn, nome)
            
        elif opcao == "6":
            break
            
        else:
            print("Opção inválida. Tente novamente.")