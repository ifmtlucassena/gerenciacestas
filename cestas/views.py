from django.shortcuts import render, redirect
from django.http import JsonResponse
from autenticacao.database import conectar_banco
import json
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from datetime import date
def listarCestas(request):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    busca = request.GET.get('busca', '')
    id_usuario = request.session.get('id_usuario')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        query_cestas = """
            SELECT Id_cesta, Nome, Preco_venda, URL_imagem, Descricao, Observacoes FROM Cesta
            WHERE Id_cesta IN (
                SELECT DISTINCT cp.Id_cesta FROM Cesta_Produto cp, Produto p, Categoria c
                WHERE cp.id_produto = p.id_produto
                AND p.id_categoria = c.id_categoria
                AND c.id_usuario = %(id_usuario)s
            )
        """
        parametros = {'id_usuario': id_usuario}

        if busca:
            query_cestas += " AND LOWER(Nome) LIKE %(busca)s"
            parametros['busca'] = f"%{busca.lower()}%"
        
        query_cestas += " ORDER BY Nome"
        
        cursor.execute(query_cestas, parametros)
        
        cestas_base = cursor.fetchall()
        cestas = []

        for cesta_item in cestas_base:
            id_cesta = cesta_item[0]
            
            query_produtos = """
                SELECT cat.nome, cat.cor
                FROM Cesta_Produto cp, Produto p, Categoria cat
                WHERE cp.id_cesta = %s
                AND cp.id_produto = p.id_produto
                AND p.id_categoria = cat.id_categoria
            """
            cursor.execute(query_produtos, (id_cesta,))
            produtos_da_cesta = cursor.fetchall()
            
            total_produtos = len(produtos_da_cesta)
            categorias_info_set = set()
            for prod in produtos_da_cesta:
                categorias_info_set.add(f"{prod[0]}:{prod[1]}")

            categorias_info = []
            for cat_info in list(categorias_info_set):
                nome, cor = cat_info.split(':', 1)
                categorias_info.append({'nome': nome, 'cor': cor})

            cestas.append({
                'id': cesta_item[0],
                'nome': cesta_item[1],
                'preco_venda': cesta_item[2] if cesta_item[2] else 0,
                'url_imagem': cesta_item[3] if cesta_item[3] else '',
                'descricao': cesta_item[4] if cesta_item[4] else '',
                'observacoes': cesta_item[5] if cesta_item[5] else '',
                'total_produtos': total_produtos,
                'categorias': categorias_info
            })

        cursor.close()
        conexao.close()
        
        sucesso = request.session.pop('sucesso', None)
        erro = request.session.pop('erro', None)
        
        context = {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'cestas': cestas,
            'busca_atual': busca,
            'sucesso': sucesso,
            'erro': erro
        }
        return render(request, 'cestas/index.html', context)
        
    except Exception as e:
        return render(request, 'cestas/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': f'Erro ao carregar cestas: {str(e)}',
            'cestas': []
        })

def novaCesta(request):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        preco_venda = request.POST.get('preco_venda')
        descricao = request.POST.get('descricao', '')
        observacoes = request.POST.get('observacoes', '')
        produtos_json = request.POST.get('produtos_selecionados', '[]')
        
        try:
            produtos_selecionados = json.loads(produtos_json)
        except:
            produtos_selecionados = []
        
        if not nome or not preco_venda:
            return render(request, 'cestas/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Nome e preço são obrigatórios',
                'titulo': 'Nova Cesta',
                'acao': 'criar'
            })
        
        try:
            preco_venda = float(preco_venda.replace(',', '.'))
        except ValueError:
            return render(request, 'cestas/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Preço deve ser um número válido',
                'titulo': 'Nova Cesta',
                'acao': 'criar'
            })
        
        url_imagem = ''
        if 'imagem_upload' in request.FILES and request.FILES['imagem_upload']:
            imagem = request.FILES['imagem_upload']
            fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'static', 'img'))
            filename = fs.save(imagem.name, imagem)
            url_imagem = f'/static/img/{filename}'
        else:
            url_imagem = request.POST.get('url_imagem', '')
        
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            
            cursor.execute(
                """INSERT INTO Cesta (Nome, Preco_venda, URL_imagem, Descricao, Observacoes, Dt_criacao) 
                   VALUES (%(nome)s, %(preco_venda)s, %(url_imagem)s, %(descricao)s, %(observacoes)s, %(dt_criacao)s)
                   RETURNING Id_cesta""",
                {
                    'nome': nome,
                    'preco_venda': preco_venda,
                    'url_imagem': url_imagem,
                    'descricao': descricao,
                    'observacoes': observacoes,
                    'dt_criacao': date.today()
                }
            )
            
            id_cesta = cursor.fetchone()[0]
            
            for produto in produtos_selecionados:
                cursor.execute(
                    """INSERT INTO Cesta_Produto (Id_cesta, Id_produto, Quantidade)
                       VALUES (%(id_cesta)s, %(id_produto)s, %(quantidade)s)""",
                    {
                        'id_cesta': id_cesta,
                        'id_produto': produto['id'],
                        'quantidade': produto['quantidade']
                    }
                )
            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            request.session['sucesso'] = 'Cesta criada com sucesso!'
            return redirect('cestas')
            
        except Exception as e:
            return render(request, 'cestas/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': f'Erro ao criar cesta: {str(e)}',
                'titulo': 'Nova Cesta',
                'acao': 'criar'
            })
    
    return render(request, 'cestas/form.html', {
        'nome_usuario': request.session.get('nome', 'Usuário'),
        'titulo': 'Nova Cesta',
        'acao': 'criar'
    })

def editarCesta(request, id_cesta):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        preco_venda = request.POST.get('preco_venda')
        descricao = request.POST.get('descricao', '')
        observacoes = request.POST.get('observacoes', '')
        produtos_json = request.POST.get('produtos_selecionados', '[]')
        
        try:
            produtos_selecionados = json.loads(produtos_json)
        except:
            produtos_selecionados = []
        
        if not nome or not preco_venda:
            cesta_atual = obterCestaPorId(id_cesta)
            return render(request, 'cestas/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Nome e preço são obrigatórios',
                'titulo': 'Editar Cesta',
                'acao': 'editar',
                'cesta_id': id_cesta,
                'cesta': cesta_atual
            })
        
        try:
            preco_venda = float(preco_venda.replace(',', '.'))
        except ValueError:
            cesta_atual = obterCestaPorId(id_cesta)
            return render(request, 'cestas/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Preço deve ser um número válido',
                'titulo': 'Editar Cesta',
                'acao': 'editar',
                'cesta_id': id_cesta,
                'cesta': cesta_atual
            })
        
        url_imagem = ''
        if 'imagem_upload' in request.FILES and request.FILES['imagem_upload']:
            imagem = request.FILES['imagem_upload']
            fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'static', 'img'))
            filename = fs.save(imagem.name, imagem)
            url_imagem = f'/static/img/{filename}'
        else:
            url_imagem = request.POST.get('url_imagem', '')
        
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            
            cursor.execute(
                "SELECT Preco_venda FROM Cesta WHERE Id_cesta = %(id_cesta)s",
                {'id_cesta': id_cesta}
            )
            preco_anterior = cursor.fetchone()[0]
            
            cursor.execute(
                """UPDATE Cesta SET Nome = %(nome)s, Preco_venda = %(preco_venda)s,
                   URL_imagem = %(url_imagem)s, Descricao = %(descricao)s,
                   Observacoes = %(observacoes)s, DT_Atualizacao_preco = %(dt_atualizacao)s,
                   Preco_venda_anterior = %(preco_anterior)s
                   WHERE Id_cesta = %(id_cesta)s""",
                {
                    'nome': nome,
                    'preco_venda': preco_venda,
                    'url_imagem': url_imagem,
                    'descricao': descricao,
                    'observacoes': observacoes,
                    'dt_atualizacao': date.today() if preco_anterior != preco_venda else None,
                    'preco_anterior': preco_anterior if preco_anterior != preco_venda else None,
                    'id_cesta': id_cesta
                }
            )
            
            cursor.execute(
                "DELETE FROM Cesta_Produto WHERE Id_cesta = %(id_cesta)s",
                {'id_cesta': id_cesta}
            )
            
            for produto in produtos_selecionados:
                cursor.execute(
                    """INSERT INTO Cesta_Produto (Id_cesta, Id_produto, Quantidade)
                       VALUES (%(id_cesta)s, %(id_produto)s, %(quantidade)s)""",
                    {
                        'id_cesta': id_cesta,
                        'id_produto': produto['id'],
                        'quantidade': produto['quantidade']
                    }
                )
            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            request.session['sucesso'] = 'Cesta atualizada com sucesso!'
            return redirect('cestas')
            
        except Exception as e:
            cesta_atual = obterCestaPorId(id_cesta)
            return render(request, 'cestas/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': f'Erro ao atualizar cesta: {str(e)}',
                'titulo': 'Editar Cesta',
                'acao': 'editar',
                'cesta_id': id_cesta,
                'cesta': cesta_atual
            })
    
    cesta = obterCestaPorId(id_cesta)
    if cesta:
        return render(request, 'cestas/form.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'titulo': 'Editar Cesta',
            'acao': 'editar',
            'cesta_id': id_cesta,
            'cesta': cesta
        })
    else:
        request.session['erro'] = 'Cesta não encontrada'
        return redirect('cestas')

def confirmarExclusao(request, id_cesta):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    cesta = obterCestaPorId(id_cesta)
    if cesta:
        return render(request, 'cestas/confirmar_exclusao.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'cesta': {
                'id': id_cesta,
                'nome': cesta['nome']
            }
        })
    else:
        request.session['erro'] = 'Cesta não encontrada'
        return redirect('cestas')

def excluirCesta(request, id_cesta):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("SELECT COUNT(*) FROM Venda WHERE Id_cesta = %(id_cesta)s", {'id_cesta': id_cesta})
        if cursor.fetchone()[0] > 0:
            cursor.close()
            conexao.close()
            request.session['erro'] = 'Não é possível excluir esta cesta, pois ela já está vinculada a um pedido existente.'
            return redirect('cestas')

        cursor.execute("DELETE FROM Cesta_Produto WHERE Id_cesta = %(id_cesta)s", {'id_cesta': id_cesta})
        cursor.execute("DELETE FROM Cesta WHERE Id_cesta = %(id_cesta)s", {'id_cesta': id_cesta})
        
        conexao.commit()
        cursor.close()
        conexao.close()
        
        request.session['sucesso'] = 'Cesta excluída com sucesso!'
        return redirect('cestas')
        
    except Exception as e:
        conexao.close()
        request.session['erro'] = f'Erro ao excluir cesta: {str(e)}'
        return redirect('cestas')

def buscarProdutos(request):
    if 'id_usuario' not in request.session:
        return JsonResponse({'erro': 'Não autorizado'}, status=401)
    
    busca = request.GET.get('busca', '')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        query = """
            SELECT p.Id_produto, p.Nome, p.Preco_custo, p.URL_imagem,
                   c.nome, c.cor
            FROM Produto p, Categoria c
            WHERE p.Id_categoria = c.id_categoria
            AND c.id_usuario = %(id_usuario)s
        """
        parametros = {'id_usuario': request.session['id_usuario']}
        
        if busca:
            query += " AND LOWER(p.Nome) LIKE %(busca)s"
            parametros['busca'] = f"%{busca.lower()}%"
        
        query += " ORDER BY p.Nome"
        
        cursor.execute(query, parametros)
        
        produtos = []
        for linha in cursor.fetchall():
            produtos.append({
                'id': linha[0],
                'nome': linha[1],
                'preco': float(linha[2]) if linha[2] else 0,
                'url_imagem': linha[3] if linha[3] else '',
                'categoria_nome': linha[4],
                'categoria_cor': linha[5]
            })
        
        cursor.close()
        conexao.close()
        
        return JsonResponse({'produtos': produtos})
        
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)

def visualizarCesta(request, id_cesta):
    if 'id_usuario' not in request.session:
        return JsonResponse({'erro': 'Não autorizado'}, status=401)
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute(
            """SELECT c.Nome, c.Preco_venda, c.URL_imagem, c.Descricao, c.Observacoes
               FROM Cesta c
               WHERE c.Id_cesta = %(id_cesta)s""",
            {'id_cesta': id_cesta}
        )
        
        cesta_info = cursor.fetchone()
        if not cesta_info:
            return JsonResponse({'erro': 'Cesta não encontrada'}, status=404)
        
        cursor.execute(
            """SELECT p.Id_produto, p.Nome, p.Preco_custo, p.URL_imagem,
                      cp.Quantidade, cat.nome, cat.cor
               FROM Cesta_Produto cp, Produto p, Categoria cat
               WHERE cp.Id_cesta = %(id_cesta)s
               AND cp.Id_produto = p.Id_produto
               AND p.Id_categoria = cat.id_categoria
               ORDER BY cat.nome, p.Nome""",
            {'id_cesta': id_cesta}
        )
        
        produtos = []
        categorias_count = {}
        
        for linha in cursor.fetchall():
            produtos.append({
                'id': linha[0],
                'nome': linha[1],
                'preco': float(linha[2]) if linha[2] else 0,
                'url_imagem': linha[3] if linha[3] else '',
                'quantidade': linha[4],
                'categoria_nome': linha[5],
                'categoria_cor': linha[6],
                'subtotal': float(linha[2] * linha[4]) if linha[2] else 0
            })
            
            cat_key = f"{linha[5]}:{linha[6]}"
            if cat_key not in categorias_count:
                categorias_count[cat_key] = {'nome': linha[5], 'cor': linha[6], 'count': 0}
            categorias_count[cat_key]['count'] += 1
        
        cursor.close()
        conexao.close()
        
        cesta = {
            'nome': cesta_info[0],
            'preco_venda': float(cesta_info[1]) if cesta_info[1] else 0,
            'url_imagem': cesta_info[2] if cesta_info[2] else '',
            'descricao': cesta_info[3] if cesta_info[3] else '',
            'observacoes': cesta_info[4] if cesta_info[4] else '',
            'produtos': produtos,
            'categorias_resumo': list(categorias_count.values()),
            'total_produtos': len(produtos),
        }
        
        return render(request, 'cestas/detalhes_modal.html', {'cesta': cesta})
        
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)

def obterCestaPorId(id_cesta):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute(
            """SELECT Nome, Preco_venda, URL_imagem, Descricao, Observacoes
               FROM Cesta WHERE Id_cesta = %(id_cesta)s""",
            {'id_cesta': id_cesta}
        )
        
        cesta = cursor.fetchone()
        if not cesta:
            return None
        
        cursor.execute(
            """SELECT p.Id_produto, p.Nome, p.Preco_custo, p.URL_imagem,
                      cp.Quantidade, cat.nome, cat.cor
               FROM Cesta_Produto cp, Produto p, Categoria cat
               WHERE cp.Id_cesta = %(id_cesta)s
               AND cp.Id_produto = p.Id_produto
               AND p.Id_categoria = cat.id_categoria""",
            {'id_cesta': id_cesta}
        )
        
        produtos = []
        for linha in cursor.fetchall():
            produtos.append({
                'id': linha[0],
                'nome': linha[1],
                'preco': float(linha[2]) if linha[2] else 0,
                'url_imagem': linha[3] if linha[3] else '',
                'quantidade': linha[4],
                'categoria_nome': linha[5],
                'categoria_cor': linha[6]
            })
        
        cursor.close()
        conexao.close()
        
        return {
            'nome': cesta[0],
            'preco_venda': float(cesta[1]) if cesta[1] else 0,
            'url_imagem': cesta[2] if cesta[2] else '',
            'descricao': cesta[3] if cesta[3] else '',
            'observacoes': cesta[4] if cesta[4] else '',
            'produtos': produtos
        }
    except:
        return None