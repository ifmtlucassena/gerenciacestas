from django.shortcuts import render
from autenticacao.database import conectar_banco

def listarCategorias(request):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute(
            "SELECT id_categoria, nome, cor, observacao FROM categoria WHERE id_usuario = %(id_usuario)s ORDER BY nome",
            {'id_usuario': request.session['id_usuario']}
        )
        
        categorias = []
        for linha in cursor.fetchall():
            categorias.append({
                'id': linha[0],
                'nome': linha[1],
                'cor': linha[2],
                'observacao': linha[3] if linha[3] else ''
            })
        
        cursor.close()
        conexao.close()
        
        return render(request, 'categorias/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'categorias': categorias
        })
        
    except Exception as e:
        return render(request, 'categorias/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': f'Erro ao carregar categorias: {str(e)}',
            'categorias': []
        })

def novaCategoria(request):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema!'
        })
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        cor = request.POST.get('cor')
        observacao = request.POST.get('observacao', '')
        
        if not nome or not cor:
            return render(request, 'categorias/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Nome e cor são obrigatórios',
                'titulo': 'Nova Categoria',
                'acao': 'criar'
            })
        
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            
            cursor.execute(
                """INSERT INTO categoria (nome, cor, observacao, id_usuario) 
                   VALUES (%(nome)s, %(cor)s, %(observacao)s, %(id_usuario)s)""",
                {
                    'nome': nome,
                    'cor': cor,
                    'observacao': observacao,
                    'id_usuario': request.session['id_usuario']
                }
            )
            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            return render(request, 'categorias/index.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'sucesso': 'Categoria criada com sucesso!',
                'categorias': obterCategorias(request.session['id_usuario'])
            })
            
        except Exception as e:
            return render(request, 'categorias/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': f'Erro ao criar categoria: {str(e)}',
                'titulo': 'Nova Categoria',
                'acao': 'criar'
            })
    
    return render(request, 'categorias/form.html', {
        'nome_usuario': request.session.get('nome', 'Usuário'),
        'titulo': 'Nova Categoria',
        'acao': 'criar'
    })

def editarCategoria(request, id_categoria):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema!'
        })
    
    # Verificar se a categoria pertence ao usuário
    if not verificarPropriedadeCategoria(id_categoria, request.session['id_usuario']):
        return render(request, 'categorias/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': 'Categoria não encontrada ou você não tem permissão para editá-la!',
            'categorias': obterCategorias(request.session['id_usuario'])
        })
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        cor = request.POST.get('cor')
        observacao = request.POST.get('observacao', '')
        
        if not nome or not cor:
            categoria_atual = obterCategoriaPorId(id_categoria, request.session['id_usuario'])
            return render(request, 'categorias/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': 'Nome e cor são obrigatórios!',
                'titulo': 'Editar Categoria',
                'acao': 'editar',
                'categoria_id': id_categoria,
                'categoria': categoria_atual
            })
        
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            
            cursor.execute(
                """UPDATE categoria SET nome = %(nome)s, cor = %(cor)s, observacao = %(observacao)s
                   WHERE id_categoria = %(id_categoria)s AND id_usuario = %(id_usuario)s""",
                {
                    'nome': nome,
                    'cor': cor,
                    'observacao': observacao,
                    'id_categoria': id_categoria,
                    'id_usuario': request.session['id_usuario']
                }
            )
            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            return render(request, 'categorias/index.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'sucesso': 'Categoria editada com sucesso!',
                'categorias': obterCategorias(request.session['id_usuario'])
            })
            
        except Exception as e:
            categoria_atual = obterCategoriaPorId(id_categoria, request.session['id_usuario'])
            return render(request, 'categorias/form.html', {
                'nome_usuario': request.session.get('nome', 'Usuário'),
                'erro': f'Erro ao editar categoria: {str(e)}',
                'titulo': 'Editar Categoria',
                'acao': 'editar',
                'categoria_id': id_categoria,
                'categoria': categoria_atual
            })
    
    categoria = obterCategoriaPorId(id_categoria, request.session['id_usuario'])
    if categoria:
        return render(request, 'categorias/form.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'titulo': 'Editar Categoria',
            'acao': 'editar',
            'categoria_id': id_categoria,
            'categoria': categoria
        })
    else:
        return render(request, 'categorias/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': 'Categoria não encontrada',
            'categorias': obterCategorias(request.session['id_usuario'])
        })

def confirmarExclusao(request, id_categoria):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    # Verificar se a categoria pertence ao usuário
    if not verificarPropriedadeCategoria(id_categoria, request.session['id_usuario']):
        return render(request, 'categorias/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': 'Categoria não encontrada ou você não tem permissão para excluí-la',
            'categorias': obterCategorias(request.session['id_usuario'])
        })
    
    categoria = obterCategoriaPorId(id_categoria, request.session['id_usuario'])
    if categoria:
        return render(request, 'categorias/confirmar_exclusao.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'categoria': {
                'id': id_categoria,
                'nome': categoria['nome']
            }
        })
    else:
        return render(request, 'categorias/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': 'Categoria não encontrada',
            'categorias': obterCategorias(request.session['id_usuario'])
        })

def excluirCategoria(request, id_categoria):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema!'
        })
    
    # Verificar se a categoria pertence ao usuário
    if not verificarPropriedadeCategoria(id_categoria, request.session['id_usuario']):
        return render(request, 'categorias/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': 'Categoria não encontrada ou você não tem permissão para excluí-la!',
            'categorias': obterCategorias(request.session['id_usuario'])
        })
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute(
            "DELETE FROM categoria WHERE id_categoria = %(id_categoria)s AND id_usuario = %(id_usuario)s",
            {
                'id_categoria': id_categoria,
                'id_usuario': request.session['id_usuario']
            }
        )
        
        conexao.commit()
        cursor.close()
        conexao.close()
        
        return render(request, 'categorias/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'sucesso': 'Categoria excluída com sucesso!',
            'categorias': obterCategorias(request.session['id_usuario'])
        })
        
    except Exception as e:
        return render(request, 'categorias/index.html', {
            'nome_usuario': request.session.get('nome', 'Usuário'),
            'erro': f'Erro ao excluir categoria: {str(e)}',
            'categorias': obterCategorias(request.session['id_usuario'])
        })

def obterCategorias(id_usuario):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute(
            "SELECT id_categoria, nome, cor, observacao FROM categoria WHERE id_usuario = %(id_usuario)s ORDER BY nome",
            {'id_usuario': id_usuario}
        )
        
        categorias = []
        for linha in cursor.fetchall():
            categorias.append({
                'id': linha[0],
                'nome': linha[1],
                'cor': linha[2],
                'observacao': linha[3] if linha[3] else ''
            })
        
        cursor.close()
        conexao.close()
        
        return categorias
    except:
        return []

def obterCategoriaPorId(id_categoria, id_usuario):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute(
            "SELECT nome, cor, observacao FROM categoria WHERE id_categoria = %(id_categoria)s AND id_usuario = %(id_usuario)s",
            {
                'id_categoria': id_categoria,
                'id_usuario': id_usuario
            }
        )
        
        categoria = cursor.fetchone()
        cursor.close()
        conexao.close()
        
        if categoria:
            return {
                'nome': categoria[0],
                'cor': categoria[1],
                'observacao': categoria[2] if categoria[2] else ''
            }
        return None
    except:
        return None

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