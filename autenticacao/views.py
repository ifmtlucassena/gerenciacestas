import hashlib
from django.shortcuts import render
from autenticacao.database import conectar_banco

def visualizarTelaCadastro(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        if not nome or not email or not senha:
            return render(request, 'autenticacao/cadastro.html',{
                'erro': 'Todos os campos são obrigatórios'
            })
        
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute(
                "SELECT id_usuario FROM usuario WHERE email = %(email)s",
                {'email': email}
            )

            if cursor.fetchone():
                cursor.close()
                conexao.close()
                return render(request, 'autenticacao/cadastro.html',{
                    'erro': 'Este email já está cadastrado'
                })

            senha_hash = hashlib.sha256(senha.encode()).hexdigest()

            cursor.execute(
                """
                INSERT INTO usuario (nome, email, senha, tipo_usuario, ativo)
                VALUES (%(nome)s, %(email)s, %(senha)s, %(tipo_usuario)s, %(ativo)s)
                """,
                {
                    'nome': nome,
                    'email': email,
                    'senha': senha_hash,
                    'tipo_usuario': 1,
                    'ativo': 1
                }
            )

            conexao.commit()
            cursor.close()
            conexao.close()

            return render(request, 'autenticacao/cadastro.html',{
                'sucesso': 'Cadastro realizado com sucesso! Você já pode fazer login.'
            })
        except Exception as e:
            return render(request, 'autenticacao/cadastro.html',{
                'erro': f'Erro ao cadastrar: {str(e)}'
            })

    return render(request, 'autenticacao/cadastro.html')

def visualizarTelaLogin(request):
    return render(request, 'autenticacao/login.html')
