from django.shortcuts import render

def visualizarDashboard(request):
    if 'id_usuario' not in request.session:
        return render(request, 'autenticacao/login.html', {
            'erro': 'Você precisa fazer login para acessar o sistema'
        })
    
    # Pega o nome da sessão
    nome_usuario = request.session.get('nome', 'Usuário')
    
    return render(request, 'dashboard/index.html', {
        'nome_usuario': nome_usuario
    })

def logout(request):
    # Limpa a sessão
    request.session.flush()
    return render(request, 'autenticacao/login.html', {
        'sucesso': 'Logout realizado com sucesso!'
    })
