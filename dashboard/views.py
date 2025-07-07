from django.shortcuts import render, redirect
from autenticacao.database import conectar_banco
from decimal import Decimal

def visualizarDashboard(request):
    if 'id_usuario' not in request.session:
        return redirect('login')

    nome_usuario = request.session.get('nome', 'Usuário')
    id_usuario = request.session.get('id_usuario')
    context = {'nome_usuario': nome_usuario}

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Card: Total de Produtos do usuário
        cursor.execute("""
            SELECT COUNT(p.Id_produto)
            FROM Produto p, Categoria c
            WHERE p.id_categoria = c.id_categoria AND c.id_usuario = %s
        """, (id_usuario,))
        context['total_produtos'] = cursor.fetchone()[0]

        # Card: Total de Categorias do usuário
        cursor.execute("SELECT COUNT(Id_categoria) FROM Categoria WHERE id_usuario = %s", (id_usuario,))
        context['total_categorias'] = cursor.fetchone()[0]

        # Card: Total de Cestas Montadas do usuário
        cursor.execute("""
            SELECT COUNT(Id_cesta) FROM Cesta WHERE Id_cesta IN (
                SELECT DISTINCT cp.Id_cesta FROM Cesta_Produto cp, Produto p, Categoria c
                WHERE cp.id_produto = p.id_produto
                AND p.id_categoria = c.id_categoria
                AND c.id_usuario = %s
            )
        """, (id_usuario,))
        context['total_cestas'] = cursor.fetchone()[0]

        # Card: Produtos com Estoque Baixo do usuário
        cursor.execute("""
            SELECT COUNT(p.Id_produto)
            FROM Produto p, Categoria c
            WHERE p.id_categoria = c.id_categoria AND c.id_usuario = %s AND p.qnt_estoque < 5
        """, (id_usuario,))
        context['total_estoque_baixo'] = cursor.fetchone()[0]

        # Financeiro: Valor Total em Estoque do usuário
        cursor.execute("""
            SELECT p.Preco_custo, p.qnt_estoque
            FROM Produto p, Categoria c
            WHERE p.id_categoria = c.id_categoria AND c.id_usuario = %s
        """, (id_usuario,))
        produtos_estoque = cursor.fetchall()
        valor_total_estoque = sum(p[0] * p[1] for p in produtos_estoque if p[0] is not None and p[1] is not None)
        context['valor_total_estoque'] = valor_total_estoque

        # Financeiro: Ticket Médio de Venda do usuário
        cursor.execute("""
            SELECT AVG(Valor_total) FROM Venda WHERE Id_cesta IN (
                SELECT DISTINCT cp.Id_cesta FROM Cesta_Produto cp, Produto p, Categoria c
                WHERE cp.id_produto = p.id_produto
                AND p.id_categoria = c.id_categoria
                AND c.id_usuario = %s
            )
        """, (id_usuario,))
        ticket_medio = cursor.fetchone()[0]
        context['ticket_medio'] = ticket_medio if ticket_medio else Decimal('0.00')

        # Financeiro: Valor Total em Cestas do usuário
        cursor.execute("""
            SELECT SUM(Preco_venda) FROM Cesta WHERE Id_cesta IN (
                SELECT DISTINCT cp.Id_cesta FROM Cesta_Produto cp, Produto p, Categoria c
                WHERE cp.id_produto = p.id_produto
                AND p.id_categoria = c.id_categoria
                AND c.id_usuario = %s
            )
        """, (id_usuario,))
        valor_total_cestas = cursor.fetchone()[0]
        context['valor_total_cestas'] = valor_total_cestas if valor_total_cestas else Decimal('0.00')

        # Tabela: Últimas Cestas Criadas do usuário
        cursor.execute("""
            SELECT Nome, Preco_venda, Dt_criacao FROM Cesta WHERE Id_cesta IN (
                SELECT DISTINCT cp.Id_cesta FROM Cesta_Produto cp, Produto p, Categoria c
                WHERE cp.id_produto = p.id_produto
                AND p.id_categoria = c.id_categoria
                AND c.id_usuario = %s
            ) ORDER BY Dt_criacao DESC, Id_cesta DESC LIMIT 5
        """, (id_usuario,))
        context['ultimas_cestas'] = cursor.fetchall()

        # Tabela: Produtos com Estoque Baixo do usuário
        cursor.execute("""
            SELECT p.Nome, c.nome, p.qnt_estoque
            FROM Produto p, Categoria c
            WHERE p.id_categoria = c.id_categoria AND c.id_usuario = %s AND p.qnt_estoque < 5
            ORDER BY p.qnt_estoque ASC, p.Nome ASC LIMIT 5
        """, (id_usuario,))
        context['produtos_estoque_baixo'] = cursor.fetchall()

        cursor.close()
        conexao.close()
    
    except Exception as e:
        context['erro'] = f"Erro ao carregar os dados do dashboard: {str(e)}"

    return render(request, 'dashboard/index.html', context)

def logout(request):
    request.session.flush()
    return redirect('login')