-- Geração de Modelo físico
-- Sql ANSI 2003 - brModelo.


CREATE TABLE Usuario (
Id_usuario SERIAL PRIMARY KEY,
Nome VARCHAR(140),
Email VARCHAR(150),
Senha VARCHAR(60),
Tipo_usuario CHAR(1),
Ativo CHAR(1)
);

CREATE TABLE Cesta (
Id_cesta SERIAL PRIMARY KEY,
Nome VARCHAR(140),
Descricao VARCHAR(255),
Observações VARCHAR(255),
Preco_venda NUMERIC(9,2),
URL_imagem VARCHAR(450),
Dt_criacao DATE,
DT_Atualizacao_preco DATE,
Preco_venda_anterior NUMERIC(9,2)
);

CREATE TABLE Categoria (
Id_categoria SERIAL PRIMARY KEY,
Nome VARCHAR(100),
Observacao VARCHAR(255),
cor VARCHAR(7),
Id_usuario INTEGER,
FOREIGN KEY(Id_usuario) REFERENCES Usuario (Id_usuario)
);

CREATE TABLE Produto (
Id_produto SERIAL PRIMARY KEY,
Nome VARCHAR(140),
Descricao VARCHAR(255),
Preco_custo NUMERIC(9,2),
qnt_estoque INTEGER,
URL_imagem VARCHAR(450),
Id_categoria INTEGER,
FOREIGN KEY(Id_categoria) REFERENCES Categoria (Id_categoria)
);

CREATE TABLE Cliente (
Id_cliente SERIAL PRIMARY KEY,
Nome VARCHAR(110),
Email VARCHAR(150),
Telefone VARCHAR(20)
);

CREATE TABLE Venda (
Id_venda SERIAL PRIMARY KEY,
Valor_total NUMERIC(9,2),
Quantidade INTEGER,
Presente CHAR(1),
Status CHAR(1),
Dt_venda DATE,
Id_cesta INTEGER,
Id_cliente INTEGER,
FOREIGN KEY(Id_cesta) REFERENCES Cesta (Id_cesta),
FOREIGN KEY(Id_cliente) REFERENCES Cliente (Id_cliente)
);

CREATE TABLE Cesta_Produto (
Id_cesta SERIAL,
Id_produto SERIAL,
Quantidade INTEGER,
PRIMARY KEY(Id_cesta,Id_produto),
FOREIGN KEY(Id_cesta) REFERENCES Cesta (Id_cesta),
FOREIGN KEY(Id_produto) REFERENCES Produto (Id_produto)
);
