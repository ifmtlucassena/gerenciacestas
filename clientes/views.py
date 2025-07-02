from django.shortcuts import render, redirect
from autenticacao.database import conectar_banco
from decimal import Decimal

def listarClientes(request):
    if 'id_usuario' not in request.session:
        return redirect('login')

    busca = request.GET.get('busca', '')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        query = "SELECT Id_cliente, Nome, Email, Telefone FROM Cliente"
        parametros = {}
        
        if busca:
            query += " WHERE LOWER(Nome) LIKE %(busca)s OR LOWER(Email) LIKE %(busca)s"
            parametros['busca'] = f"%{busca.lower()}%"
            
        query += " ORDER BY Nome"
        
        cursor.execute(query, parametros)
        
        clientes = []
        for linha in cursor.fetchall():
            clientes.append({
                'id': linha[0],
                'nome': linha[1],
                'email': linha[2],
                'telefone': linha[3]
            })
            
        cursor.close()
        conexao.close()

        context = {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'clientes': clientes,
            'busca_atual': busca,
            'sucesso': request.session.pop('sucesso', None),
            'erro': request.session.pop('erro', None)
        }
        return render(request, 'clientes/index.html', context)

    except Exception as e:
        context = {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': f'Erro ao carregar clientes: {str(e)}',
            'clientes': []
        }
        return render(request, 'clientes/index.html', context)

def novoCliente(request):
    if 'id_usuario' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        
        form_data = {'nome': nome, 'email': email, 'telefone': telefone}

        if not nome:
            context = {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'O campo Nome é obrigatório.',
                'titulo': 'Novo Cliente', 'acao': 'criar', 'cliente': form_data
            }
            return render(request, 'clientes/form.html', context)

        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()

            if email:
                cursor.execute("SELECT Id_cliente FROM Cliente WHERE Email = %s", (email,))
                if cursor.fetchone():
                    cursor.close()
                    conexao.close()
                    context = {
                        'nome_usuario': request.session.get('nome', 'Usuário'),
                        'erro': 'Este e-mail já está cadastrado.',
                        'titulo': 'Novo Cliente', 'acao': 'criar', 'cliente': form_data
                    }
                    return render(request, 'clientes/form.html', context)

            cursor.execute(
                "INSERT INTO Cliente (Nome, Email, Telefone) VALUES (%s, %s, %s)",
                (nome, email, telefone)
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            request.session['sucesso'] = 'Cliente criado com sucesso!'
            return redirect('clientes')
        except Exception as e:
            context = {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': f'Erro ao criar cliente: {str(e)}',
                'titulo': 'Novo Cliente', 'acao': 'criar', 'cliente': form_data
            }
            return render(request, 'clientes/form.html', context)
    
    context = {
        'nome_usuario': request.session.get('nome', 'Usuário'),
        'titulo': 'Novo Cliente',
        'acao': 'criar'
    }
    return render(request, 'clientes/form.html', context)

def editarCliente(request, id_cliente):
    if 'id_usuario' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        
        cliente_atual = obterClientePorId(id_cliente)
        
        if not nome:
            context = {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'O campo Nome é obrigatório.',
                'titulo': 'Editar Cliente', 'acao': 'editar', 'cliente': cliente_atual
            }
            return render(request, 'clientes/form.html', context)

        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()

            if email:
                cursor.execute("SELECT Id_cliente FROM Cliente WHERE Email = %s AND Id_cliente != %s", (email, id_cliente))
                if cursor.fetchone():
                    cursor.close()
                    conexao.close()
                    context = {
                        'nome_usuario': request.session.get('nome', 'Usuário'),
                        'erro': 'Este e-mail já pertence a outro cliente.',
                        'titulo': 'Editar Cliente', 'acao': 'editar', 'cliente': cliente_atual
                    }
                    return render(request, 'clientes/form.html', context)

            cursor.execute(
                "UPDATE Cliente SET Nome = %s, Email = %s, Telefone = %s WHERE Id_cliente = %s",
                (nome, email, telefone, id_cliente)
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            request.session['sucesso'] = 'Cliente atualizado com sucesso!'
            return redirect('clientes')
        except Exception as e:
            context = {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': f'Erro ao atualizar cliente: {str(e)}',
                'titulo': 'Editar Cliente', 'acao': 'editar', 'cliente': cliente_atual
            }
            return render(request, 'clientes/form.html', context)
    
    cliente = obterClientePorId(id_cliente)
    if not cliente:
        request.session['erro'] = 'Cliente não encontrado.'
        return redirect('clientes')

    context = {
        'nome_usuario': request.session.get('nome', 'Usuário'),
        'titulo': 'Editar Cliente',
        'acao': 'editar',
        'cliente': cliente
    }
    return render(request, 'clientes/form.html', context)

def visualizarCliente(request, id_cliente):
    if 'id_usuario' not in request.session:
        return redirect('login')
        
    cliente = obterClientePorId(id_cliente)
    if not cliente:
        request.session['erro'] = 'Cliente não encontrado.'
        return redirect('clientes')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("SELECT Valor_total FROM Venda WHERE Id_cliente = %s", (id_cliente,))
        vendas = cursor.fetchall()
        total_pedidos = len(vendas)
        faturamento_total = sum(venda[0] for venda in vendas if venda[0] is not None)

        query_cestas = """
            SELECT c.Nome, COUNT(v.Id_cesta)
            FROM Venda v, Cesta c
            WHERE v.Id_cliente = %s AND v.Id_cesta = c.Id_cesta
            GROUP BY c.Nome
            ORDER BY COUNT(v.Id_cesta) DESC
            LIMIT 5
        """
        cursor.execute(query_cestas, (id_cliente,))
        cestas_favoritas = cursor.fetchall()

        cursor.close()
        conexao.close()

        context = {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'cliente': cliente,
            'total_pedidos': total_pedidos,
            'faturamento_total': faturamento_total,
            'cestas_favoritas': cestas_favoritas
        }
        return render(request, 'clientes/detalhes_cliente.html', context)

    except Exception as e:
        request.session['erro'] = f"Erro ao carregar detalhes do cliente: {e}"
        return redirect('clientes')

def confirmarExclusaoCliente(request, id_cliente):
    if 'id_usuario' not in request.session:
        return redirect('login')
        
    cliente = obterClientePorId(id_cliente)
    if not cliente:
        request.session['erro'] = 'Cliente não encontrado.'
        return redirect('clientes')

    context = {
        'nome_usuario': request.session.get('nome', 'Usuário'),
        'cliente': cliente
    }
    return render(request, 'clientes/confirmar_exclusao.html', context)

def excluirCliente(request, id_cliente):
    if 'id_usuario' not in request.session:
        return redirect('login')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute("DELETE FROM Venda WHERE Id_cliente = %s", (id_cliente,))
        cursor.execute("DELETE FROM Cliente WHERE Id_cliente = %s", (id_cliente,))

        conexao.commit()
        cursor.close()
        conexao.close()
        request.session['sucesso'] = 'Cliente e todos os seus pedidos foram excluídos com sucesso!'
    except Exception as e:
        request.session['erro'] = f'Erro ao excluir cliente: {str(e)}'
        
    return redirect('clientes')

def obterClientePorId(id_cliente):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("SELECT Id_cliente, Nome, Email, Telefone FROM Cliente WHERE Id_cliente = %s", (id_cliente,))
        cliente_data = cursor.fetchone()
        cursor.close()
        conexao.close()
        if cliente_data:
            return {
                'id': cliente_data[0],
                'nome': cliente_data[1],
                'email': cliente_data[2],
                'telefone': cliente_data[3]
            }
        return None
    except:
        return None