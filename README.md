# Projeto "Build-to-Learn" com uso Real

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092e20.svg?style=for-the-badge&logo=django&logoColor=white)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=for-the-badge)

### STATUS: Em desenvolvimento

## INTRODUÇÃO

Este é um projeto que está sendo desenvolvido com o intuito de **aprender** mais sobre a construção de **softwares reais**, e que servirá ainda para o uso diário de um microempreendedor para organização de suas vendas.

A ideia é construir um software **ERP**, que ajudará o empreendedor a organizar seus clientes, produtos e histórico de vendas.


## Principais observações

Ao me aprofundar no desenvolvimento desse software, com o tempo fui notando a importância de diversos pontos como: **Arquiteturas**, **Regras de negócios**, **Segurança** e **Robustez**.

A escolha da Linguagem **Python** se dá ao fato de ser a linguagem que uso como porta de entrada para o desenvolvimento de software, e o uso do framework **Django** pois é um framework bem completo para aplicações web.

---

## Stack

- **Python 3.13** + **Django 6**
- **PostgreSQL** (produção) / **SQLite** (desenvolvimento)
- **Whitenoise** para arquivos estáticos
- **Gunicorn** como servidor WSGI
- **Poetry** para gerenciamento de dependências
- Deploy na plataforma **Render**

---

## Arquitetura

O projeto segue a arquitetura padrão **MVT** do Django, dividido em 4 apps:

```
carol-semi-joias/
├── semi-joias-admin/
│   ├── accounts/           # Autenticação (login/logout)
│   ├── clients/            # Gestão de clientes
│   ├── sales/              # Maletas, produtos, vendas
│   │   ├── models.py
│   │   ├── choices.py      # Enumerações centralizadas
│   │   ├── forms.py
│   │   ├── urls.py
│   │   ├── views/
│   │   │   ├── maleta_view.py
│   │   │   ├── produtos_view.py
│   │   │   └── vendas_view.py
│   │   └── services/
│   │       └── models_filter.py
│   ├── mysite/             # Configurações do projeto
│   ├── templates/          # Templates globais (base.html)
│   └── tests/              # Suíte de testes
├── pyproject.toml
└── build.sh
```

### `accounts`
Autenticação de usuários. Login com redirecionamento, logout via POST. Usuários são criados e gerenciados exclusivamente pelo Django Admin.

### `clients`
Cadastro e gestão de clientes. Expõe as propriedades `full_name` e `formatted_phone`. As vendas de um cliente são acessíveis a partir da listagem de clientes.

### `sales`
Núcleo do sistema. Dividido em três domínios:

- **Maletas** — Lotes de produtos enviados pelo fornecedor, com período de vendas e valor da ordem.
- **Produtos** — Itens dentro de cada maleta, com controle de estoque automático.
- **Vendas** — Fluxo completo: criação via wizard, parcelas, devoluções e garantias.

---

## Modelos

### `Maleta`
| Campo | Descrição |
|---|---|
| `month` | Mês de referência |
| `start_sale_period` / `end_sale_period` | Período de vendas |
| `order_number` | Número único da ordem |
| `order_value` | Valor total da ordem |
| `value_sold` | Valor vendido — calculado automaticamente excluindo vendas canceladas |

### `Produtos`
| Campo | Descrição |
|---|---|
| `product_briefcase` | FK para Maleta |
| `product_code` | Código único por maleta |
| `product_quantity` | Estoque total |
| `quantity_sold` | Quantidade vendida — controlado automaticamente |
| `remaining_quantity` | Property: `product_quantity - quantity_sold` |

### `Vendas`
| Campo | Descrição |
|---|---|
| `client` | FK para Cliente |
| `briefcase` | FK para Maleta |
| `payment_method` | `pix`, `debito`, `credito`, `dinheiro` |
| `installments` | Número de parcelas (opcional) |
| `in_good_standing` | `adimplente` ou `inadimplente` |
| `status` | `ativa`, `cancelada`, `devolvida_parcial` |
| `sale_value` / `discount` / `end_value` | Calculados automaticamente a partir dos itens |

### Outros modelos
- **`ItensVenda`** — Produto, quantidade, preço e descontos de uma venda. Único por `(sale, product)`.
- **`Parcela`** — Geradas automaticamente. Situações: `pendente`, `pago`, `cancelada`.
- **`Devolucao` / `ItemDevolucao`** — Registro de devoluções com restauração proporcional de estoque.
- **`Garantia`** — Registro de garantias por item. Status: `enviado` → `em_analise` → `resolvido` / `recusado`.

---

## Fluxo de Criação de Venda

A criação segue um wizard de 3 passos baseado em sessão. Nenhuma escrita no banco ocorre até a confirmação final:

```
Passo 1 — Itens       → /vendas/registrar_venda/<maleta_id>/
Passo 2 — Verificação → /vendas/nova/<maleta_id>/verificar/
Passo 3 — Dados       → /vendas/nova/<maleta_id>/dados/
```

No passo 3, a venda, os itens e as parcelas são salvos atomicamente em uma única transação. Uma vez criada, a venda é **imutável** — itens não podem ser adicionados, editados ou removidos.

---

## Regras de Negócio

- **Estoque**: Controlado via `select_for_update()` dentro de `transaction.atomic()`, evitando race conditions em acessos simultâneos.
- **Imutabilidade**: Após criação, as ações disponíveis sobre uma venda são: atualizar situação de pagamento, registrar devolução, registrar garantia e cancelar.
- **Cancelamento**: Irreversível. Restaura estoque de todos os itens e cancela todas as parcelas.
- **Devolução**: Parcial ou total. Cada item tem controle da quantidade já devolvida. Estoque é restaurado proporcionalmente.
- **Garantia**: Ciclo de status gerenciado manualmente: `Enviado → Em Análise → Resolvido / Recusado`.
- **Parcelas**: Geradas automaticamente e distribuídas proporcionalmente. Para pagamento em crédito, o controle de parcelas não é exibido (gerenciado pelo banco emissor).
- **Produto**: Não pode ser excluído se houver itens de venda vinculados. `product_quantity` não pode ser reduzido abaixo de `quantity_sold`.
- **Maleta**: Não pode ser excluída se houver vendas registradas.

---

## Configuração Local

**Pré-requisitos:** Python 3.13+ e [Poetry](https://python-poetry.org/)

```bash
git clone <repo>
cd carol-semi-joias
poetry install
```

Crie um arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=sua-chave-secreta
DATABASE_URL=sqlite:///db.sqlite3
```

Execute:

```bash
cd semi-joias-admin
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
poetry run python manage.py runserver
```

Acesse `http://localhost:8000`. O login é obrigatório — use o superusuário criado acima.

---

## Testes

```bash
# Rodar toda a suíte
poetry run pytest

# Com verbosidade
poetry run pytest --verbosity=2

# Classe específica
poetry run pytest tests/test_sales.py::TestCancelarVenda -v
```

A suíte cobre models, views e regras de negócio. Todos os testes de view utilizam `force_login` para autenticação.

---

## Deploy (Render)

O deploy é realizado automaticamente via `build.sh`.

**Variáveis de ambiente necessárias:**

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta do Django |
| `DATABASE_URL` | URL de conexão com o PostgreSQL |
| `RENDER` | Qualquer valor — ativa `DEBUG=False` |
| `RENDER_EXTERNAL_HOSTNAME` | Hostname do serviço — adicionado ao `ALLOWED_HOSTS` |

Gerenciamento de usuários feito pelo Django Admin.
