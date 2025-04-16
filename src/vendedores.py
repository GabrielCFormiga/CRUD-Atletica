from psycopg2 import Error

############################################################################################################
# MÉTODOS DE VALIDAÇÃO
############################################################################################################

def validar_matricula(matricula):
    """
    Critérios:
    - Contém apenas dígitos.
    - Tamanho entre 6 e 20 caracteres.
    """
    matricula = matricula.strip()
    return matricula.isdigit() and 6 <= len(matricula) <= 20

def validar_nome(nome):
    """
    Critérios:
    - Contém apenas letras e espaços.
    - Tamanho mínimo de 3 caracteres.
    """
    return all(c.isalpha() or c.isspace() for c in nome) and len(nome) >= 3

def validar_email(email):
    """
    Critérios:
    - Contém o caractere '@'.
    - Contém um '.' após o '@'.
    - Tamanho mínimo de 5 caracteres.
    """
    return '@' in email and '.' in email.split('@')[-1] and len(email) >= 5

def validar_telefone(telefone):
    """
    Critérios:
    - Aceita números no formato (XX) XXXXX-XXXX ou similar.
    - Tamanho entre 10 e 11 dígitos após remover caracteres não numéricos.
    """
    telefone = ''.join(filter(str.isdigit, telefone))
    return 10 <= len(telefone) <= 11

############################################################################################################
# MÉTODOS DE BUSCA
############################################################################################################

def buscar_vendedor_por_matricula(conn, matricula):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vendedores WHERE matricula = %s", (matricula,))
        vendedor = cursor.fetchone()
        return vendedor
    except Error as e:
        print(f"Erro ao buscar vendedor: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

def buscar_vendedor_por_nome(conn, nome):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT matricula, nome, email, telefone, ativo 
            FROM vendedores 
            WHERE nome ILIKE %s 
            ORDER BY nome
        """, (f"%{nome}%",))
        vendedores = cursor.fetchall()
        
        if vendedores:
            print("\n╭───────────────────────────────────────────────────────────────────────────────────────────────────╮")
            print(f"│ {'Matrícula':<12} │ {'Nome':<25} │ {'Email':<25} │ {'Telefone':<15} │ {'Status':<8} │")
            print("├──────────────┼───────────────────────────┼───────────────────────────┼─────────────────┼──────────┤")
            
            for vendedor in vendedores:
                matricula, nome, email, telefone, ativo = vendedor
                status = "Ativo" if ativo else "Inativo"
                print(f"│ {matricula:<12} │ {nome[:25]:<25} │ {email[:25]:<25} │ {telefone:<15} │ {status:<8} │")
            
            print("╰──────────────┴───────────────────────────┴───────────────────────────┴─────────────────┴──────────╯")
            print(f"\nTotal encontrado: {len(vendedores)} vendedor(es)")
        else:
            print("\nNenhum vendedor encontrado com esse nome.")
            
    except Error as e:
        print(f"\nErro ao buscar vendedor: {e}")
    finally:
        if cursor:
            cursor.close()

############################################################################################################
# MÉTODOS DE CRUD
############################################################################################################

def criar_vendedor(conn):
    """
    Fluxo:
    - Solicita matrícula, nome, email, telefone e status de atividade.
    - Valida os dados fornecidos.
    - Insere o vendedor no banco de dados.
    """
    print("\n--- Cadastro de Vendedor ---")
    
    # Validação da matrícula
    while True:
        matricula = input("Matrícula: ").strip()
        if not validar_matricula(matricula):
            print("Matrícula inválida! Deve conter apenas números (6-20 dígitos).")
            continue
        
        if buscar_vendedor_por_matricula(conn, matricula):
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
            cursor.execute("SELECT 1 FROM vendedores WHERE email = %s", (email,))
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
    
    # Validação do status de atividade
    while True:
        ativo = input("Está ativo? (S/N): ").upper()
        if ativo not in ('S', 'N'):
            print("Opção inválida! Digite S para Sim ou N para Não.")
            continue
        break
    
    # Formata os dados antes de inserir
    telefone = ''.join(filter(str.isdigit, telefone))
    ativo = ativo == 'S'
    
    # Conexão com o banco para inserção    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vendedores (matricula, nome, email, telefone, ativo)
            VALUES (%s, %s, %s, %s, %s)
        """, (matricula, nome, email, telefone, ativo))
        conn.commit()
        print("\Vendedor cadastrado com sucesso!")
        print(f"Matrícula: {matricula}")
        print(f"Nome: {nome}")
        print(f"Email: {email}")
        print(f"Telefone: {telefone}")
        print(f"Status: {'Ativo' if ativo else 'Inativo'}")
    except Error as e:
        conn.rollback()
        print(f"\nErro ao cadastrar vendedor: {e}")
    finally:
        if cursor:
            cursor.close()

def listar_vendedores(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT matricula, nome, email, telefone, ativo FROM vendedores ORDER BY nome")
        vendedores = cursor.fetchall()
        
        if vendedores:
            print("\n╭───────────────────────────────────────────────────────────────────────────────────────────────────╮")
            print(f"│ {'Matrícula':<12} │ {'Nome':<25} │ {'Email':<25} │ {'Telefone':<15} │ {'Status':<8} │")
            print("├──────────────┼───────────────────────────┼───────────────────────────┼─────────────────┼──────────┤")
            
            for vendedor in vendedores:
                matricula, nome, email, telefone, ativo = vendedor
                status = "Ativo" if ativo else "Inativo"
                print(f"│ {matricula:<12} │ {nome[:25]:<25} │ {email[:25]:<25} │ {telefone:<15} │ {status:<8} │")
            
            print("╰──────────────┴───────────────────────────┴───────────────────────────┴─────────────────┴──────────╯")
            print(f"\nTotal de vendedores cadastrados: {len(vendedores)}")
        else:
            print("\nNenhum vendedor cadastrado no sistema.")

    except Error as e:
        print(f"\nErro ao listar vendedores: {e}")
    finally:
        if cursor:
            cursor.close()

def atualizar_vendedor(conn):
    print("\n--- Atualização de Vendedor ---")
    
    # Busca pelo vendedor
    matricula = input("Digite a matrícula do vendedor: ").strip()
    vendedor = buscar_vendedor_por_matricula(conn, matricula)
    
    if not vendedor:
        print("\nVendedor não encontrado!")
        return
    
    # Exibe os dados atuais
    print("\nDados atuais do vendedor:")
    print(f"Matrícula: {vendedor[0]}")
    print(f"Nome: {vendedor[1]}")
    print(f"Email: {vendedor[2]}")
    print(f"Telefone: {vendedor[3]}")
    print(f"Status: {'Ativo' if vendedor[4] else 'Inativo'}")
    
    # Atualização dos campos
    print("\nDeixe em branco para manter o valor atual")
    
    # Nome
    while True:
        novo_nome = input(f"\nNovo nome [{vendedor[1]}]: ").strip()
        if not novo_nome:
            novo_nome = vendedor[1]
            break
        if validar_nome(novo_nome):
            break
        print("Nome inválido! Deve conter apenas letras e espaços (mínimo 3 caracteres).")
    
    # Email
    while True:
        novo_email = input(f"\nNovo email [{vendedor[2]}]: ").strip()
        if not novo_email:
            novo_email = vendedor[2]
            break
        if validar_email(novo_email):
            if novo_email != vendedor[2]:  # Só verifica se mudou
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 1 FROM vendedores 
                        WHERE email = %s AND matricula != %s
                    """, (novo_email, matricula))
                    if cursor.fetchone():
                        print("Email já está em uso por outro vendedor!")
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
        novo_telefone = input(f"\nNovo telefone [{vendedor[3]}]: ").strip()
        if not novo_telefone:
            novo_telefone = vendedor[3]
            break
        if validar_telefone(novo_telefone):
            novo_telefone = ''.join(filter(str.isdigit, novo_telefone))
            break
        print("Telefone inválido! Use o formato (XX) XXXXX-XXXX ou similar.")
    
    # Status
    while True:
        novo_status = input(f"\nAtivo? [{'S' if vendedor[4] else 'N'}] (S/N): ").upper().strip()
        if not novo_status:
            novo_status = 'S' if vendedor[4] else 'N'
            break
        if novo_status in ('S', 'N'):
            break
        print("Opção inválida! Digite S para Sim ou N para Não.")
    
    # Confirmação
    print("\nDados a serem atualizados:")
    print(f"Nome: {novo_nome}")
    print(f"Email: {novo_email}")
    print(f"Telefone: {novo_telefone}")
    print(f"Status: {'Ativo' if novo_status == 'S' else 'Inativo'}")
    
    confirmacao = input("\nConfirmar atualização? (S/N): ").upper()
    if confirmacao != 'S':
        print("Atualização cancelada!")
        return
    
    # Executa a atualização
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE vendedores
            SET nome = %s, email = %s, telefone = %s, ativo = %s
            WHERE matricula = %s
        """, (novo_nome, novo_email, novo_telefone, novo_status == 'S', matricula))
        conn.commit()
        print("\nVendedor atualizado com sucesso!")
    except Error as e:
        conn.rollback()
        print(f"\nErro ao atualizar vendedor: {e}")
    finally:
        if cursor:
            cursor.close()

def deletar_vendedor(conn, matricula):
    try:
        cursor = conn.cursor()
        
        # Verifica se o vendedor está associado a alguma venda
        cursor.execute("""
            SELECT 1 FROM vendedor_vendas 
            WHERE vendedor_matricula = %s 
            LIMIT 1
        """, (matricula,))
        
        if cursor.fetchone():
            print("\nEste vendedor está associado a vendas e não pode ser removido!")
            return
        
        # Executa a remoção
        cursor.execute("DELETE FROM vendedores WHERE matricula = %s", (matricula,))
        conn.commit()
        
        if cursor.rowcount > 0:
            print("\nVendedor removido com sucesso!")
        else:
            print("\nNenhum vendedor encontrado com essa matrícula!")
            
    except Error as e:
        conn.rollback()
        print(f"\nErro ao remover vendedor: {e}")
    finally:
        if cursor:
            cursor.close()

############################################################################################################
# MÉTODOS DE MENU
############################################################################################################

def menu_vendedores(conn):
    while True:
        print("\n=== MENU DE VENDEDORES ===")
        print("1. Cadastrar novo vendedor")
        print("2. Listar todos os vendedores")
        print("3. Atualizar vendedor")
        print("4. Remover vendedor")
        print("5. Buscar vendedor por nome")
        print("6. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            criar_vendedor(conn)
        elif opcao == "2":
            listar_vendedores(conn)
        elif opcao == "3":
            atualizar_vendedor(conn)
        elif opcao == "4":
            matricula = input("\nMatrícula do vendedor a remover: ")
            vendedor = buscar_vendedor_por_matricula(conn, matricula)
            if vendedor:
                confirmacao = input(f"Tem certeza que deseja remover {vendedor[1]}? (S/N): ").upper()
                if confirmacao == "S":
                    deletar_vendedor(conn, matricula)
            else:
                print("Vendedor não encontrado!")
        elif opcao == "5":
            nome = input("\nNome do vendedor a buscar: ")
            buscar_vendedor_por_nome(conn, nome)
        elif opcao == "6":
            break
        else:
            print("Opção inválida. Tente novamente.")

