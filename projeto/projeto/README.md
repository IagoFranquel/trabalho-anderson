# Sistema de Vendas – Projeto de Banco de Dados

## Identificação

- **Aluno:** Iago Frânquel Freitas Sousa
- **Disciplina:** Projeto de Banco de Dados
- **Professor:** Anderson

## Sobre o projeto

Aplicação web de vendas que evolui um CRUD (clientes e produtos) para um sistema que usa o banco de dados para **processar** as informações, e não apenas armazená-las.

O problema que resolve: registrar vendas garantindo, de forma atômica, a validação de estoque, a baixa do estoque, o cálculo de desconto e o histórico de movimentações, além de oferecer relatórios consolidados de vendas e da situação do estoque.

## Tecnologias utilizadas

- Python 3 + Flask
- PostgreSQL (SGBD)
- psycopg2
- HTML/CSS/JavaScript

## Banco de dados

**SGBD:** PostgreSQL 12 ou superior

**Principais tabelas:** `clientes`, `produtos`, `vendas`, `itens_venda`, `movimentacoes_estoque`

| Recurso | Nome | Finalidade | Onde é usado na aplicação |
|---|---|---|---|
| View | `vw_relatorio_vendas` | Junta vendas, clientes e itens em um relatório consolidado | Tela **Relatório de Vendas** |
| View | `vw_estoque_situacao` | Classifica o estoque (OK / BAIXO / ESGOTADO) e soma o total vendido | Telas **Estoque** e **Nova Venda** (lista de produtos) |
| Function | `fn_calcular_desconto(cliente_id, subtotal)` | Regra de desconto: VIP 10% + 5% para subtotal ≥ R$ 500 | Prévia de desconto na tela **Nova Venda** (`/api/desconto`) e dentro da procedure de venda |
| Procedure | `sp_realizar_venda(cliente_id, produto_ids[], quantidades[])` | Registra a venda inteira: valida estoque, grava itens, baixa estoque, registra movimentação, calcula total | Botão **Confirmar venda** da tela **Nova Venda** |
| Procedure | `sp_cancelar_venda(venda_id)` | Cancela a venda e devolve os itens ao estoque | Botão **Cancelar** do **Relatório de Vendas** |

## Estrutura do repositório

```
/projeto
├── /src                  código da aplicação (Flask)
├── /database
│   ├── /tables           criação das tabelas
│   ├── /views            views
│   ├── /functions        functions
│   ├── /procedures       procedures
│   └── /inserts          dados de teste
├── /docs                 roteiro do vídeo
└── README.md
```

## Como executar

1. Instale o PostgreSQL e crie o banco:
   ```sql
   CREATE DATABASE loja_db;
   ```
2. Instale as dependências:
   ```bash
   cd src
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Configure a conexão (opcional – valores padrão entre parênteses):
   ```bash
   export DB_HOST=localhost       # (localhost)
   export DB_PORT=5432            # (5432)
   export DB_NAME=loja_db         # (loja_db)
   export DB_USER=postgres        # (postgres)
   export DB_PASSWORD=sua_senha   # (postgres)
   ```
   No Windows (PowerShell): `$env:DB_PASSWORD="sua_senha"`.
4. Crie as tabelas, view, function, procedures e dados de teste:
   ```bash
   python init_db.py
   ```
   Alternativa: executar manualmente, nesta ordem, os `.sql` de `database/tables`, `views`, `functions`, `procedures` e `inserts`.
5. Rode a aplicação:
   ```bash
   python app.py
   ```
6. Acesse http://127.0.0.1:5000

## Alternativa: usar o Supabase (sem instalar PostgreSQL)

1. Crie uma conta e um projeto em https://supabase.com (guarde a senha do banco).
2. No projeto, clique em **Connect** e copie a string **Session pooler** (formato `postgresql://postgres.xxxx:[YOUR-PASSWORD]@aws-0-regiao.pooler.supabase.com:5432/postgres`). Substitua `[YOUR-PASSWORD]` pela sua senha.
3. Defina a variável e rode normalmente (passos 2, 4, 6 e 7 acima, pulando a criação do banco):
   ```bash
   export DATABASE_URL="postgresql://postgres.xxxx:SENHA@aws-0-regiao.pooler.supabase.com:5432/postgres"
   python init_db.py
   python app.py
   ```
   No Windows (PowerShell): `$env:DATABASE_URL="postgresql://..."`
4. Se a senha tiver caracteres especiais (`@`, `#`, `/`, `:`), troque por códigos de URL (`@` = `%40`, `#` = `%23`, `/` = `%2F`, `:` = `%3A`) ou use uma senha só com letras e números.
5. Opcional: as tabelas, a view, a function e as procedures aparecem no painel do Supabase em **Table Editor** e **Database**, o que ajuda na demonstração do vídeo.
 **Vídeo:** https://youtu.be/DC_rN21dBm0
## Como testar os recursos

- **View:** abra *Relatório de Vendas* e *Estoque*.
- **Function:** em *Nova Venda*, escolha um cliente VIP e adicione produtos; o desconto muda conforme o cliente e o subtotal.
- **Procedure:** confirme uma venda e veja o estoque baixar; tente vender mais que o estoque disponível para ver o erro vindo do banco; cancele uma venda e veja o estoque voltar.
