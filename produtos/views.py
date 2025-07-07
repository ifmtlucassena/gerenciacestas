from django.shortcuts import render, redirect
from autenticacao.database import conectar_banco

def listarProdutos(request):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    busca = request.GET.get('busca', '')
    categoria_filtro = request.GET.get('categoria', '')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        query = """
            SELECT Prod.Id_produto, Prod.Nome, Prod.Descricao, Prod.Preco_custo, 
                   Prod.qnt_estoque, Prod.URL_imagem, Prod.Id_categoria,
                   Cat.nome, Cat.cor
            FROM Produto Prod, Categoria Cat
            WHERE Prod.Id_categoria = Cat.id_categoria 
            AND Cat.id_usuario = %(id_usuario)s
        """
        parametros = {'id_usuario': request.session['id_usuario']}
        
        if busca:
            query += " AND LOWER(Prod.Nome) LIKE %(busca)s"
            parametros['busca'] = f"%{busca.lower()}%"
        
        if categoria_filtro:
            query += " AND Prod.Id_categoria = %(categoria_filtro)s"
            parametros['categoria_filtro'] = categoria_filtro
            
        query += " ORDER BY Prod.Nome"
        
        cursor.execute(query, parametros)
        
        produtos = []
        for linha in cursor.fetchall():
            total_estoque = linha[3] * linha[4] if linha[3] and linha[4] else 0
            produtos.append({
                'id': linha[0],
                'nome': linha[1],
                'descricao': linha[2] if linha[2] else '',
                'preco_custo': linha[3] if linha[3] else 0,
                'qnt_estoque': linha[4] if linha[4] else 0,
                'url_imagem': linha[5] if linha[5] else '',
                'id_categoria': linha[6],
                'categoria_nome': linha[7],
                'categoria_cor': linha[8],
                'total_estoque': total_estoque
            })
        
        categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
        
        cursor.close()
        conexao.close()
        
        sucesso = request.session.pop('sucesso', None)
        erro = request.session.pop('erro', None)
        
        context = {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'produtos': produtos,
            'categorias': categorias,
            'busca_atual': busca,
            'categoria_atual': categoria_filtro
        }
        
        if sucesso:
            context['sucesso'] = sucesso
        if erro:
            context['erro'] = erro
            
        return render(request, 'produtos/index.html', context)
        
    except Exception as e:
        return render(request, 'produtos/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': f'Erro ao carregar produtos: {str(e)}',
            'produtos': [],
            'categorias': []
        })

def novoProduto(request):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        preco_custo = request.POST.get('preco_custo')
        qnt_estoque = request.POST.get('qnt_estoque')
        url_imagem = request.POST.get('url_imagem', '')
        id_categoria = request.POST.get('id_categoria')
        
        if not nome or not preco_custo or not qnt_estoque or not id_categoria:
            categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
            return render(request, 'produtos/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Nome, preço, estoque e categoria são obrigatórios',
                'titulo': 'Novo Produto',
                'acao': 'criar',
                'categorias': categorias
            })
        
        if not verificarPropriedadeCategoria(id_categoria, request.session['id_usuario']):
            categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
            return render(request, 'produtos/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Categoria inválida',
                'titulo': 'Novo Produto',
                'acao': 'criar',
                'categorias': categorias
            })
        
        try:
            preco_custo = float(preco_custo.replace(',', '.'))
            qnt_estoque = int(qnt_estoque)
        except ValueError:
            categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
            return render(request, 'produtos/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Preço e estoque devem ser números válidos',
                'titulo': 'Novo Produto',
                'acao': 'criar',
                'categorias': categorias
            })
        
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            
            cursor.execute(
                """INSERT INTO Produto (Nome, Descricao, Preco_custo, qnt_estoque, URL_imagem, Id_categoria) 
                   VALUES (%(nome)s, %(descricao)s, %(preco_custo)s, %(qnt_estoque)s, %(url_imagem)s, %(id_categoria)s)""",
                {
                    'nome': nome,
                    'descricao': descricao,
                    'preco_custo': preco_custo,
                    'qnt_estoque': qnt_estoque,
                    'url_imagem': url_imagem,
                    'id_categoria': id_categoria
                }
            )
            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            request.session['sucesso'] = 'Produto criado com sucesso!'
            return redirect('produtos')
            
        except Exception as e:
            categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
            return render(request, 'produtos/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': f'Erro ao criar produto: {str(e)}',
                'titulo': 'Novo Produto',
                'acao': 'criar',
                'categorias': categorias
            })
    
    categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
    return render(request, 'produtos/form.html', {
        'nome_usuario': request.session.get('nome', 'Usuário'),
        'titulo': 'Novo Produto',
        'acao': 'criar',
        'categorias': categorias
    })

def editarProduto(request, id_produto):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    if not verificarPropriedadeProduto(id_produto, request.session['id_usuario']):
        request.session['erro'] = 'Produto não encontrado ou você não tem permissão para editá-lo'
        return redirect('produtos')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        preco_custo = request.POST.get('preco_custo')
        qnt_estoque = request.POST.get('qnt_estoque')
        url_imagem = request.POST.get('url_imagem', '')
        id_categoria = request.POST.get('id_categoria')
        
        if not nome or not preco_custo or not qnt_estoque or not id_categoria:
            produto_atual = obterProdutoPorId(id_produto, request.session['id_usuario'])
            categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
            return render(request, 'produtos/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Nome, preço, estoque e categoria são obrigatórios',
                'titulo': 'Editar Produto',
                'acao': 'editar',
                'produto_id': id_produto,
                'produto': produto_atual,
                'categorias': categorias
            })
        
        if not verificarPropriedadeCategoria(id_categoria, request.session['id_usuario']):
            produto_atual = obterProdutoPorId(id_produto, request.session['id_usuario'])
            categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
            return render(request, 'produtos/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Categoria inválida',
                'titulo': 'Editar Produto',
                'acao': 'editar',
                'produto_id': id_produto,
                'produto': produto_atual,
                'categorias': categorias
            })
        
        try:
            preco_custo = float(preco_custo.replace(',', '.'))
            qnt_estoque = int(qnt_estoque)
        except ValueError:
            produto_atual = obterProdutoPorId(id_produto, request.session['id_usuario'])
            categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
            return render(request, 'produtos/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Preço e estoque devem ser números válidos',
                'titulo': 'Editar Produto',
                'acao': 'editar',
                'produto_id': id_produto,
                'produto': produto_atual,
                'categorias': categorias
            })
        
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            
            cursor.execute(
                """UPDATE Produto SET Nome = %(nome)s, Descricao = %(descricao)s, 
                   Preco_custo = %(preco_custo)s, qnt_estoque = %(qnt_estoque)s, 
                   URL_imagem = %(url_imagem)s, Id_categoria = %(id_categoria)s
                   WHERE Id_produto = %(id_produto)s""",
                {
                    'nome': nome,
                    'descricao': descricao,
                    'preco_custo': preco_custo,
                    'qnt_estoque': qnt_estoque,
                    'url_imagem': url_imagem,
                    'id_categoria': id_categoria,
                    'id_produto': id_produto
                }
            )
            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            request.session['sucesso'] = 'Produto editado com sucesso!'
            return redirect('produtos')
            
        except Exception as e:
            produto_atual = obterProdutoPorId(id_produto, request.session['id_usuario'])
            categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
            return render(request, 'produtos/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': f'Erro ao editar produto: {str(e)}',
                'titulo': 'Editar Produto',
                'acao': 'editar',
                'produto_id': id_produto,
                'produto': produto_atual,
                'categorias': categorias
            })
    
    produto = obterProdutoPorId(id_produto, request.session['id_usuario'])
    categorias = obterCategoriasDoUsuario(request.session['id_usuario'])
    
    if produto:
        return render(request, 'produtos/form.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'titulo': 'Editar Produto',
            'acao': 'editar',
            'produto_id': id_produto,
            'produto': produto,
            'categorias': categorias
        })
    else:
        request.session['erro'] = 'Produto não encontrado'
        return redirect('produtos')

def confirmarExclusao(request, id_produto):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    if not verificarPropriedadeProduto(id_produto, request.session['id_usuario']):
        request.session['erro'] = 'Produto não encontrado ou você não tem permissão para excluí-lo'
        return redirect('produtos')
    
    produto = obterProdutoPorId(id_produto, request.session['id_usuario'])
    if produto:
        return render(request, 'produtos/confirmar_exclusao.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'produto': {
                'id': id_produto,
                'nome': produto['nome']
            }
        })
    else:
        request.session['erro'] = 'Produto não encontrado'
        return redirect('produtos')

def excluirProduto(request, id_produto):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    if not verificarPropriedadeProduto(id_produto, request.session['id_usuario']):
        request.session['erro'] = 'Produto não encontrado ou você não tem permissão para excluí-lo'
        return redirect('produtos')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute("DELETE FROM Cesta_Produto WHERE Id_produto = %(id_produto)s", {'id_produto': id_produto})
        
        cursor.execute("DELETE FROM Produto WHERE Id_produto = %(id_produto)s", {'id_produto': id_produto})
        
        conexao.commit()
        cursor.close()
        conexao.close()
        
        request.session['sucesso'] = 'Produto excluído com sucesso!'
        return redirect('produtos')
        
    except Exception as e:
        conexao.close()
        request.session['erro'] = f'Erro ao excluir produto. O produto pode estar associado a outros registros.'
        return redirect('produtos')

def obterCategoriasDoUsuario(id_usuario):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute(
            "SELECT id_categoria, nome FROM categoria WHERE id_usuario = %(id_usuario)s ORDER BY nome",
            {'id_usuario': id_usuario}
        )
        
        categorias = []
        for linha in cursor.fetchall():
            categorias.append({
                'id': linha[0],
                'nome': linha[1]
            })
        
        cursor.close()
        conexao.close()
        
        return categorias
    except:
        return []

def obterProdutoPorId(id_produto, id_usuario):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute(
            """SELECT Prod.Nome, Prod.Descricao, Prod.Preco_custo, Prod.qnt_estoque, 
                      Prod.URL_imagem, Prod.Id_categoria
               FROM Produto Prod, Categoria Cat
               WHERE Prod.Id_categoria = Cat.id_categoria 
               AND Cat.id_usuario = %(id_usuario)s 
               AND Prod.Id_produto = %(id_produto)s""",
            {
                'id_produto': id_produto,
                'id_usuario': id_usuario
            }
        )
        
        produto = cursor.fetchone()
        cursor.close()
        conexao.close()
        
        if produto:
            return {
                'nome': produto[0],
                'descricao': produto[1] if produto[1] else '',
                'preco_custo': produto[2] if produto[2] else 0,
                'qnt_estoque': produto[3] if produto[3] else 0,
                'url_imagem': produto[4] if produto[4] else '',
                'id_categoria': produto[5]
            }
        return None
    except:
        return None

def verificarPropriedadeProduto(id_produto, id_usuario):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute(
            """SELECT Prod.Id_produto
               FROM Produto Prod, Categoria Cat
               WHERE Prod.Id_categoria = Cat.id_categoria 
               AND Cat.id_usuario = %(id_usuario)s 
               AND Prod.Id_produto = %(id_produto)s""",
            {
                'id_produto': id_produto,
                'id_usuario': id_usuario
            }
        )
        
        resultado = cursor.fetchone()
        cursor.close()
        conexao.close()
        
        return resultado is not None
    except:
        return False

def verificarPropriedadeCategoria(id_categoria, id_usuario):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute(
            "SELECT id_categoria FROM categoria WHERE id_categoria = %(id_categoria)s AND id_usuario = %(id_usuario)s",
            {
                'id_categoria': id_categoria,
                'id_usuario': id_usuario
            }
        )
        
        resultado = cursor.fetchone()
        cursor.close()
        conexao.close()
        
        return resultado is not None
    except:
        return False
