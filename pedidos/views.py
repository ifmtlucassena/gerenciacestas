from django.shortcuts import render, redirect
from django.http import JsonResponse
from autenticacao.database import conectar_banco
from datetime import date
import json

def listarPedidos(request):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {'erro': 'Você precisa fazer login para acessar o sistema'})

    busca = request.GET.get('busca', '')
    id_usuario = request.session.get('id_usuario')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        query = """
            SELECT v.Id_venda, c.Nome, cli.Nome, v.Quantidade, v.Valor_total, v.Dt_venda, v.Status
            FROM Venda v, Cesta c, Cliente cli
            WHERE v.Id_cesta = c.Id_cesta
            AND v.Id_cliente = cli.Id_cliente
            AND v.Id_cesta IN (
                SELECT DISTINCT cp.Id_cesta FROM Cesta_Produto cp, Produto p, Categoria cat
                WHERE cp.id_produto = p.id_produto
                AND p.id_categoria = cat.id_categoria
                AND cat.id_usuario = %(id_usuario)s
            )
        """
        parametros = {'id_usuario': id_usuario}
        
        if busca:
            query += " AND (LOWER(c.Nome) LIKE %(busca)s OR LOWER(cli.Nome) LIKE %(busca)s)"
            parametros['busca'] = f"%{busca.lower()}%"
            
        query += " ORDER BY v.Dt_venda DESC"
        
        cursor.execute(query, parametros)
        
        pedidos = []
        for linha in cursor.fetchall():
            pedidos.append({
                'id': linha[0],
                'cesta_nome': linha[1],
                'cliente_nome': linha[2],
                'quantidade': linha[3],
                'valor_total': linha[4],
                'dt_venda': linha[5],
                'status': linha[6]
            })
            
        cursor.close()
        conexao.close()

        sucesso = request.session.pop('sucesso', None)
        erro = request.session.pop('erro', None)

        context = {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'pedidos': pedidos,
            'busca_atual': busca,
            'sucesso': sucesso,
            'erro': erro,
        }
        return render(request, 'pedidos/index.html', context)

    except Exception as e:
        return render(request, 'pedidos/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': f'Erro ao carregar pedidos: {str(e)}',
            'pedidos': []
        })

def novoPedido(request):
    if 'id_usuario' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        id_cliente = request.POST.get('id_cliente')
        id_cesta = request.POST.get('id_cesta')
        quantidade = request.POST.get('quantidade')
        presente = request.POST.get('presente') == 'on'
        status = request.POST.get('status')
        dt_venda_str = request.POST.get('dt_venda')

        dt_venda = date.today()
        if dt_venda_str:
            dt_venda = dt_venda_str

        if not all([id_cliente, id_cesta, quantidade, status]):
            request.session['erro'] = 'Todos os campos são obrigatórios!'
            return redirect('novo_pedido')

        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute("SELECT Preco_venda FROM Cesta WHERE Id_cesta = %s", (id_cesta,))
            preco_cesta_result = cursor.fetchone()
            if not preco_cesta_result:
                request.session['erro'] = 'Cesta selecionada não é válida.'
                return redirect('novo_pedido')
            
            preco_cesta = preco_cesta_result[0]
            valor_total = preco_cesta * int(quantidade)

            cursor.execute(
                """
                INSERT INTO Venda (Id_cliente, Id_cesta, Quantidade, Valor_total, Presente, Status, Dt_venda)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (id_cliente, id_cesta, quantidade, valor_total, 'S' if presente else 'N', status, dt_venda)
            )
            
            conexao.commit()
            cursor.close()
            conexao.close()

            request.session['sucesso'] = 'Pedido criado com sucesso!'
            return redirect('pedidos')

        except Exception as e:
            request.session['erro'] = f'Ocorreu um erro ao criar o pedido: {str(e)}'
            return redirect('novo_pedido')

    cestas = obterCestas()
    clientes = obterClientes()
    context = {
        'nome_usuario': request.session.get('nome', 'Usuário'),
        'titulo': 'Novo Pedido',
        'acao': 'criar',
        'cestas': cestas,
        'clientes': clientes,
        'erro': request.session.pop('erro', None)
    }
    return render(request, 'pedidos/form.html', context)

def editarPedido(request, id_venda):
    if 'id_usuario' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        id_cliente = request.POST.get('id_cliente')
        id_cesta = request.POST.get('id_cesta')
        quantidade = request.POST.get('quantidade')
        presente = request.POST.get('presente') == 'on'
        status = request.POST.get('status')
        dt_venda_str = request.POST.get('dt_venda')

        dt_venda = date.today()
        if dt_venda_str:
            dt_venda = dt_venda_str

        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute("SELECT Preco_venda FROM Cesta WHERE Id_cesta = %s", (id_cesta,))
            preco_cesta = cursor.fetchone()[0]
            valor_total = preco_cesta * int(quantidade)

            cursor.execute(
                """
                UPDATE Venda SET Id_cliente = %s, Id_cesta = %s, Quantidade = %s, 
                               Valor_total = %s, Presente = %s, Status = %s, Dt_venda = %s
                WHERE Id_venda = %s
                """,
                (id_cliente, id_cesta, quantidade, valor_total, 'S' if presente else 'N', status, dt_venda, id_venda)
            )

            conexao.commit()
            cursor.close()
            conexao.close()

            request.session['sucesso'] = 'Pedido atualizado com sucesso!'
            return redirect('pedidos')
        except Exception as e:
            request.session['erro'] = f'Erro ao atualizar o pedido: {str(e)}'
            return redirect('editar_pedido', id_venda=id_venda)

    pedido = obterPedidoPorId(id_venda)
    cestas = obterCestas()
    clientes = obterClientes()
    
    dt_venda_formatada = ''
    if pedido and pedido.get('dt_venda'):
        dt_venda_formatada = pedido['dt_venda'].strftime('%Y-%m-%d')


    context = {
        'nome_usuario': request.session.get('nome', 'Usuário'),
        'titulo': 'Editar Pedido',
        'acao': 'editar',
        'pedido': pedido,
        'cestas': cestas,
        'clientes': clientes,
        'dt_venda_formatada': dt_venda_formatada,
        'erro': request.session.pop('erro', None)
    }
    return render(request, 'pedidos/form.html', context)

def excluirPedido(request, id_venda):
    if 'id_usuario' not in request.session:
        return redirect('login')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM Venda WHERE Id_venda = %s", (id_venda,))
        conexao.commit()
        cursor.close()
        conexao.close()
        request.session['sucesso'] = 'Pedido excluído com sucesso!'
    except Exception as e:
        request.session['erro'] = f'Erro ao excluir pedido: {str(e)}'
        
    return redirect('pedidos')

def confirmarExclusaoPedido(request, id_venda):
    if 'id_usuario' not in request.session:
        return redirect('login')
        
    pedido = obterPedidoPorId(id_venda, detalhado=True)
    if not pedido:
        request.session['erro'] = 'Pedido não encontrado.'
        return redirect('pedidos')

    context = {
        'nome_usuario': request.session.get('nome', 'Usuário'),
        'pedido': pedido
    }
    return render(request, 'pedidos/confirmar_exclusao.html', context)

def visualizarPedido(request, id_venda):
    if 'id_usuario' not in request.session:
        return redirect('login')

    pedido = obterPedidoPorId(id_venda, detalhado=True)
    
    context = {
        'pedido': pedido
    }
    return render(request, 'pedidos/detalhes_pedido.html', context)

def buscarClientes(request):
    if 'id_usuario' not in request.session:
        return JsonResponse({'erro': 'Não autorizado'}, status=401)
    
    busca = request.GET.get('busca', '')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        query = "SELECT Id_cliente, Nome, Email, Telefone FROM Cliente WHERE LOWER(Nome) LIKE %s"
        cursor.execute(query, (f"%{busca.lower()}%",))
        
        clientes = []
        for linha in cursor.fetchall():
            clientes.append({
                'id': linha[0],
                'nome': linha[1],
                'email': linha[2],
                'telefone': linha[3],
            })
            
        cursor.close()
        conexao.close()
        
        return JsonResponse({'clientes': clientes})
        
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)

def novoClienteRapido(request):
    if 'id_usuario' not in request.session:
        return JsonResponse({'erro': 'Não autorizado'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nome = data.get('nome')
            email = data.get('email')
            telefone = data.get('telefone')

            if not nome:
                return JsonResponse({'erro': 'Nome é obrigatório'}, status=400)

            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute(
                "INSERT INTO Cliente (Nome, Email, Telefone) VALUES (%s, %s, %s) RETURNING Id_cliente, Nome, Email, Telefone",
                (nome, email, telefone)
            )
            novo_cliente_data = cursor.fetchone()
            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            novo_cliente = {
                'id': novo_cliente_data[0],
                'nome': novo_cliente_data[1],
                'email': novo_cliente_data[2],
                'telefone': novo_cliente_data[3]
            }

            return JsonResponse({'sucesso': True, 'cliente': novo_cliente})
        except Exception as e:
            return JsonResponse({'erro': str(e)}, status=500)
    
    return JsonResponse({'erro': 'Método não permitido'}, status=405)

def obterCestas():
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("SELECT Id_cesta, Nome FROM Cesta ORDER BY Nome")
        cestas = [{'id': c[0], 'nome': c[1]} for c in cursor.fetchall()]
        cursor.close()
        conexao.close()
        return cestas
    except:
        return []

def obterClientes():
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("SELECT Id_cliente, Nome FROM Cliente ORDER BY Nome")
        clientes = [{'id': c[0], 'nome': c[1]} for c in cursor.fetchall()]
        cursor.close()
        conexao.close()
        return clientes
    except:
        return []

def obterPedidoPorId(id_venda, detalhado=False):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        if detalhado:
            query = """
                SELECT 
                    v.Id_venda, v.Quantidade, v.Valor_total, v.Presente, v.Status, v.Dt_venda,
                    c.Id_cesta, c.Nome, c.Preco_venda, c.URL_imagem,
                    cli.Id_cliente, cli.Nome, cli.Email, cli.Telefone
                FROM Venda v, Cesta c, Cliente cli
                WHERE v.Id_cesta = c.Id_cesta
                  AND v.Id_cliente = cli.Id_cliente
                  AND v.Id_venda = %s
            """
        else:
            query = "SELECT * FROM Venda WHERE Id_venda = %s"
            
        cursor.execute(query, (id_venda,))
        pedido_data = cursor.fetchone()
        cursor.close()
        conexao.close()

        if not pedido_data:
            return None

        if detalhado:
            return {
                'id': pedido_data[0],
                'quantidade': pedido_data[1],
                'valor_total': pedido_data[2],
                'presente': pedido_data[3],
                'status': pedido_data[4],
                'dt_venda': pedido_data[5],
                'cesta': {
                    'id': pedido_data[6],
                    'nome': pedido_data[7],
                    'preco_venda': pedido_data[8],
                    'url_imagem': pedido_data[9]
                },
                'cliente': {
                    'id': pedido_data[10],
                    'nome': pedido_data[11],
                    'email': pedido_data[12],
                    'telefone': pedido_data[13]
                }
            }
        else:
            return {
                'id': pedido_data[0],
                'valor_total': pedido_data[1],
                'quantidade': pedido_data[2],
                'presente': 'S' if pedido_data[3] == 'S' else 'N',
                'status': pedido_data[4],
                'dt_venda': pedido_data[5],
                'id_cesta': pedido_data[6],
                'id_cliente': pedido_data[7],
            }
            
    except Exception as e:
        print(e)
        return None