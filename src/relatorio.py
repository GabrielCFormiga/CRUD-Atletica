from psycopg2 import Error

############################################################################################################
# MÉTODOS CRUD
############################################################################################################

def relatorio_socios(conn):
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

def relatorio_estoque_baixo(conn, limite=None):
    """
    Gera relatório de produtos com estoque baixo, com limite personalizável.
    
    Parâmetros:
        conn: Conexão com o banco
        limite (int, opcional): Limite para considerar estoque baixo. Se None, usa 5 como padrão.
    
    Fluxo:
    1. Valida parâmetro limite
    2. Consulta dados do banco
    3. Exibe relatório formatado
    """
    # Define o limite padrão se não for especificado
    if limite is None:
        limite = 5
    
    # Validação do limite
    try:
        limite = int(limite)
        if limite < 1:
            print("\nErro: O limite deve ser pelo menos 1")
            return
    except ValueError:
        print("\nErro: O limite deve ser um número inteiro")
        return
    
    try:
        cursor = conn.cursor()
        
        # Consulta estatísticas gerais
        cursor.execute("SELECT * FROM vw_estoque_stats")
        stats = cursor.fetchone()
        
        # Consulta produtos com estoque baixo (usando parâmetro dinâmico)
        cursor.execute("""
            SELECT id, nome, quantidade, preco, valor_total_estoque
            FROM vw_estoque_geral
            WHERE quantidade < %s
            ORDER BY quantidade ASC, nome ASC
        """, (limite,))
        
        produtos = cursor.fetchall()

        # Cabeçalho do relatório
        print("\n=== RELATÓRIO DE ESTOQUE BAIXO ===")
        print(f"\nLimite definido: menos de {limite} unidades")
        print(f"\nTotal de produtos cadastrados: {stats[0]}")
        print(f"Total de unidades em estoque: {stats[1]}")
        print(f"Média de estoque: {stats[2]:.2f} unidades")
        print(f"Menor estoque: {stats[3]} unidades")
        print(f"Maior estoque: {stats[4]} unidades")

        # Se houver produtos com estoque baixo
        if produtos:
            print(f"\n=== PRODUTOS COM ESTOQUE ABAIXO DE {limite} UNIDADES ===")
            
            print("\n" + "=" * 90)
            print(f"{'ID':<5} | {'Nome':<30} | {'Estoque':<10} | {'Preço Unit.':<12} | {'Valor Total':<12}")
            print("-" * 90)

            for produto in produtos:
                alerta = "(!) " if produto[2] < 2 else ""  # Destaque para estoque crítico
                print(
                    f"{produto[0]:<5} | {produto[1][:30]:<30} | "
                    f"{produto[2]:<10}{alerta}| R$ {produto[3]:<10.2f} | "
                    f"R$ {produto[4]:<10.2f}"
                )

            print("=" * 90)
            print(f"Total de produtos com estoque baixo: {len(produtos)}")
            print("(!) - Estoque crítico (menos de 2 unidades)")
        else:
            print(f"\nNenhum produto com estoque abaixo de {limite} unidades.")

    except Error as e:
        print(f"\nErro ao gerar relatório: {str(e)}")
    finally:
        if cursor:
            cursor.close()

############################################################################################################
# MÉTODOS DE MENU
############################################################################################################

def menu_relatorios(conn):
    limite_padrao = 5  # Define um limite padrão
    
    while True:
        print("\n=== MENU DE RELATÓRIOS ===")
        print(f"1. Relatório de sócios")
        print(f"2. Relatório de estoque baixo (limite atual: {limite_padrao})")
        print(f"3. Configurar limite para estoque baixo")
        print(f"4. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            relatorio_socios(conn)
            
        elif opcao == "2":
            relatorio_estoque_baixo(conn, limite_padrao)
            
        elif opcao == "3":
            while True:
                try:
                    novo_limite = input(f"\nNovo limite para estoque baixo (atual: {limite_padrao}): ").strip()
                    
                    if not novo_limite:  # Se pressionar Enter sem digitar, mantém o atual
                        print(f"Mantendo o limite atual de {limite_padrao}.")
                        break
                    
                    novo_limite = int(novo_limite)
                    if novo_limite < 1:
                        print("O limite deve ser pelo menos 1.")
                        continue
                    
                    limite_padrao = novo_limite
                    print(f"\nNovo limite definido: {limite_padrao} unidades.")
                    relatorio_estoque_baixo(conn, limite_padrao)  # Mostra o relatório com novo limite
                    break
                    
                except ValueError:
                    print("Por favor, digite um número inteiro válido.")
            
        elif opcao == "4":
            break
            
        else:
            print("Opção inválida. Digite um número entre 1 e 4.")