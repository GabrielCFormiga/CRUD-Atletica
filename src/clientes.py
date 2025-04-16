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

def validar_time(time):
    """
    Critérios:
    - Deve conter apenas letras, espaços e caracteres comuns em nomes de times
    - Tamanho entre 2 e 50 caracteres
    - Não pode ser composto apenas por espaços
    """
    if not time or len(time.strip()) < 2 or len(time) > 50:
        return False
    
    caracteres_permitidos = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ áéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ-'0123456789")
    return all(c in caracteres_permitidos for c in time) and not time.isspace()

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

############################################################################################################
# MÉTODOS DE BUSCA
############################################################################################################

def buscar_cliente_por_matricula(conn, matricula):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT matricula, nome, email, telefone, eh_socio, time, cidade, assiste_op 
            FROM clientes 
            WHERE matricula = %s
        """, (matricula,))
        cliente = cursor.fetchone()
        return cliente
    except Error as e:
        print(f"Erro ao buscar cliente: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

def buscar_cliente_por_nome(conn, nome):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT matricula, nome, email, telefone, eh_socio, time, cidade, assiste_op 
            FROM clientes 
            WHERE nome ILIKE %s 
            ORDER BY nome
        """, (f"%{nome}%",))
        clientes = cursor.fetchall()
        
        if clientes:
            print("\n╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮")
            print(f"│ {'Matrícula':<12} │ {'Nome':<25} │ {'Email':<25} │ {'Telefone':<15} │ {'Status':<9} │ {'Time':<15} │ {'Cidade':<15} │ {'OP Fan':<7} │")
            print("├──────────────┼───────────────────────────┼───────────────────────────┼─────────────────┼───────────┼─────────────────┼─────────────────┼─────────┤")
            
            for cliente in clientes:
                matricula, nome, email, telefone, eh_socio, time, cidade, assiste_op = cliente
                status = "Sócio" if eh_socio else "Não-sócio"
                op_fan = "Sim" if assiste_op else "Não"
                print(f"│ {matricula:<12} │ {nome[:25]:<25} │ {email[:25]:<25} │ {telefone:<15} │ {status:<9} │ {time[:15]:<15} │ {cidade[:15]:<15} │ {op_fan:<7} │")
            
            print("╰──────────────┴───────────────────────────┴───────────────────────────┴─────────────────┴───────────┴─────────────────┴─────────────────┴─────────╯")
            print(f"\nTotal encontrado: {len(clientes)} cliente(s)")
        else:
            print("\nNenhum cliente encontrado com esse nome.")
            
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
    Fluxo:
    - Solicita matrícula, nome, email, telefone, status de sócio, time, cidade, e se assiste One Piece.
    - Valida os dados fornecidos.
    - Insere o cliente no banco de dados.
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

    # Time do coração
    while True:
        time = input("Time do coração: ").strip()
        time = time.title().strip()
        if not validar_time(time):
            print("Time inválido! Deve conter 2 a 50 caracteres (apenas letras, espaços e caracteres comuns).")
            continue
        break

    # Cidade
    while True:
        cidade = input("Cidade onde nasceu: ").strip()
        cidade = cidade.title().strip()
        if not validar_cidade(cidade):
            print("Cidade inválida! Deve conter 2 a 50 caracteres (apenas letras, espaços e hífens).")
            continue
        break

    # Assiste One Piece?
    while True:
        assiste_op = input("Assiste One Piece? (S/N): ").upper()
        if assiste_op not in ('S', 'N'):
            print("Opção inválida! Digite S para Sim ou N para Não.")
            continue
        break

    # Formata os dados antes de inserir
    telefone = ''.join(filter(str.isdigit, telefone))
    eh_socio = eh_socio == 'S'
    assiste_op = assiste_op == 'S'
    
    # Conexão com o banco para inserção    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clientes (matricula, nome, email, telefone, eh_socio, time, cidade, assiste_op)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (matricula, nome, email, telefone, eh_socio, time, cidade, assiste_op))
        conn.commit()
        print("\nCliente cadastrado com sucesso!")
        print(f"Matrícula: {matricula}")
        print(f"Nome: {nome}")
        print(f"Email: {email}")
        print(f"Telefone: {telefone}")
        print(f"Status: {'Sócio' if eh_socio else 'Não-sócio'}")
        print(f"Time: {time}")
        print(f"Cidade: {cidade}")
        print(f"Assiste One Piece: {'Sim' if assiste_op else 'Não'}")
    except Error as e:
        conn.rollback()
        print(f"\nErro ao cadastrar cliente: {e}")
    finally:
        if cursor:
            cursor.close()

def listar_clientes(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT matricula, nome, email, telefone, eh_socio, time, cidade, assiste_op 
            FROM clientes 
            ORDER BY nome
        """)
        clientes = cursor.fetchall()
        
        if clientes:
            print("\n╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮")
            print(f"│ {'Matrícula':<12} │ {'Nome':<25} │ {'Email':<25} │ {'Telefone':<15} │ {'Status':<9} │ {'Time':<15} │ {'Cidade':<15} │ {'OP Fan':<7} │")
            print("├──────────────┼───────────────────────────┼───────────────────────────┼─────────────────┼───────────┼─────────────────┼─────────────────┼─────────┤")
            
            for cliente in clientes:
                matricula, nome, email, telefone, eh_socio, time, cidade, assiste_op = cliente
                status = "Sócio" if eh_socio else "Não-sócio"
                op_fan = "Sim" if assiste_op else "Não"
                print(f"│ {matricula:<12} │ {nome[:25]:<25} │ {email[:25]:<25} │ {telefone:<15} │ {status:<9} │ {time[:15]:<15} │ {cidade[:15]:<15} │ {op_fan:<7} │")
            
            print("╰──────────────┴───────────────────────────┴───────────────────────────┴─────────────────┴───────────┴─────────────────┴─────────────────┴─────────╯")
            print(f"\nTotal de clientes cadastrados: {len(clientes)}")
        else:
            print("\nNenhum cliente cadastrado no sistema.")

    except Error as e:
        print(f"Erro ao listar clientes: {e}")
    finally:
        if cursor:
            cursor.close()

def atualizar_cliente(conn):
    """
    Fluxo:
    - Solicita a matrícula do cliente.
    - Exibe os dados atuais do cliente.
    - Permite a atualização de nome, email, telefone e status de sócio.
    - Atualiza os dados no banco de dados.
    """
    print("\n--- Atualização de Cliente ---")
    
    # Busca por matrícula
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
    print(f"Time: {cliente[5]}")
    print(f"Cidade: {cliente[6]}")
    print(f"Assiste One Piece: {'Sim' if cliente[7] else 'Não'}")
    
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

    # Time
    while True:
        novo_time = input(f"\nNovo time [{cliente[5]}]: ").strip() or cliente[5]
        novo_time = novo_time.title().strip()
        if not validar_time(novo_time):
            print("Time inválido! Deve conter 2 a 50 caracteres (apenas letras, espaços e caracteres comuns).")
            continue
        break

    # Cidade
    while True:
        nova_cidade = input(f"\nNova cidade [{cliente[6]}]: ").strip() or cliente[6]
        nova_cidade = nova_cidade.title().strip()
        if not validar_cidade(nova_cidade):
            print("Cidade inválida! Deve conter 2 a 50 caracteres (apenas letras, espaços e hífens).")
            continue
        break

    while True:
        novo_op = input(f"\nAssiste One Piece? [{'S' if cliente[7] else 'N'}] (S/N): ").upper().strip()
        if not novo_op:
            novo_op = 'S' if cliente[7] else 'N'
            break
        if novo_op in ('S', 'N'):
            break
        print("Opção inválida! Digite S para Sim ou N para Não.")
    
    # Confirmação
    print("\nDados a serem atualizados:")
    print(f"Nome: {novo_nome}")
    print(f"Email: {novo_email}")
    print(f"Telefone: {novo_telefone}")
    print(f"Status: {'Sócio' if novo_status == 'S' else 'Não-sócio'}")
    print(f"Time: {novo_time}")
    print(f"Cidade: {nova_cidade}")
    
    confirmacao = input("\nConfirmar atualização? (S/N): ").upper()
    if confirmacao != 'S':
        print("Atualização cancelada!")
        return
    
    # Executa a atualização
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clientes
            SET nome = %s, email = %s, telefone = %s, eh_socio = %s,
                time = %s, cidade = %s, assiste_op = %s
            WHERE matricula = %s
        """, (novo_nome, novo_email, novo_telefone, novo_status == 'S',
              novo_time, nova_cidade, novo_op == 'S', matricula))
        conn.commit()
        print("\nCliente atualizado com sucesso!")
    except Error as e:
        conn.rollback()
        print(f"\nErro ao atualizar cliente: {e}")
    finally:
        if cursor:
            cursor.close()

def deletar_cliente(conn, matricula):
    try:
        cursor = conn.cursor()
        
        # Verifica se o cliente possui vendas associadas
        cursor.execute("""
            SELECT 1 FROM vendas 
            WHERE cliente_matricula = %s 
            LIMIT 1
        """, (matricula,))
        
        if cursor.fetchone():
            print("\nEste cliente possui vendas associadas e não pode ser removido!")
            print("Opções:")
            print("1. Cancelar a operação")
            print("2. Ver as vendas do cliente")
            
            opcao = input("\nEscolha uma opção: ").strip()
            if opcao == "2":
                # Mostra as vendas do cliente
                cursor.execute("""
                    SELECT v.id, v.data_venda, v.valor_total, v.status
                    FROM vendas v
                    WHERE v.cliente_matricula = %s
                    ORDER BY v.data_venda DESC
                """, (matricula,))
                vendas = cursor.fetchall()
                
                print("\n╭───────────────────────────── Vendas do Cliente ──────────────────────────────╮")
                print(f"│ {'ID':<6} │ {'Data':<19} │ {'Valor Total':<12} │ {'Status':<12} │")
                print("├───────┼─────────────────────┼──────────────┼──────────────┤")
                
                for venda in vendas:
                    print(f"│ {venda[0]:<6} │ {venda[1].strftime('%d/%m/%Y %H:%M'):<19} │ R${venda[2]:<10.2f} │ {venda[3]:<12} │")
                
                print("╰───────┴─────────────────────┴──────────────┴──────────────╯")
            
            return
        
        # Se não houver vendas, prossegue com a exclusão
        cursor.execute("DELETE FROM clientes WHERE matricula = %s", (matricula,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print("\nCliente removido com sucesso!")
        else:
            print("\nNenhum cliente encontrado com essa matrícula!")
            
    except Error as e:
        conn.rollback()
        print(f"\nErro ao remover cliente: {e}")
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