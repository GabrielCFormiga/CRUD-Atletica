from psycopg2 import Error

conn = None

def menu_relatorios(conexao):
    global conn
    conn = conexao
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