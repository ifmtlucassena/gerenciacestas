from django.shortcuts import render
from autenticacao.database import conectar_banco

# Create your views here.
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
            SELECT 
            FROM Cestas Ces, Produtos
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