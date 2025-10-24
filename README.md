# Mini-WMS - Sistema de Gerenciamento de Armazém

Sistema web moderno para controle de estoque e visualização de armazém, containerizado com Docker.

## 🚀 Funcionalidades

- ✅ Visualização em grade e mapa do armazém
- ✅ Controle de entradas e saídas de estoque
- ✅ Pesquisa e filtros
- ✅ Exportação para CSV
- ✅ Interface responsiva e moderna
- ✅ Banco de dados SQLite integrado
- ✅ Importação de dados via CSV
- ✅ **NOVO:** Aba de movimentações com histórico completo
- ✅ **NOVO:** Busca combinada por localização e referência do produto
- ✅ **NOVO:** Nomes atualizados de abas ("Mapa", "Grade", "Movimentações", "Configurações")

## 🛠 Tecnologias

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Banco de Dados**: SQLite
- **Container**: Docker & Docker Compose
- **Web Server**: Nginx

## 📦 Instalação e Execução

### Pré-requisitos
- Docker
- Docker Compose

### Execução Rápida

1. Clone ou baixe os arquivos do projeto
2. Coloque seus arquivos CSV em `data/import/`:
   - `locations.csv` - Localizações do armazém (novo formato)
   - `products.csv` - Catálogo de produtos
3. Execute:
```bash
docker-compose up -d
```
4. Acesse: http://localhost:8090

### Desenvolvimento

Para desenvolvimento com hot-reload:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

## 📁 Estrutura de Arquivos

```
mini-wms/
├── data/import/           # Arquivos CSV para importação
│   ├── locations.csv      # Localizações do armazém (COD,LOCAL,ARMAZEM)
│   └── products.csv       # Catálogo de produtos
├── src/                   # Código fonte
│   ├── app.py             # Aplicação Flask principal
│   ├── database.py        # Inicialização do banco de dados
│   ├── templates/
│   │   └── index.html     # Interface web principal
│   └── static/
│       └── style.css      # Estilos da aplicação
└── docker-compose.yml     # Configuração Docker
```

## 📊 Formato dos Arquivos CSV

### locations.csv (NOVO FORMATO)
```csv
COD,LOCAL,ARMAZEM
10000,A001C,LOG
10001,A001D,LOG
10002,A002C,LOG
```

### products.csv
```csv
ref,name
P1001,CAR BOLA
P1002,CAR CHORRO
```

## 🗃 Estrutura do Banco

- **locations**: Localizações do armazém (cod, local, armazem)
- **products**: Catálogo de produtos
- **stock**: Estoque por localização
- **movements**: Histórico de movimentações

## 🔧 Melhorias Implementadas

### Interface de Usuário
- **Nova aba "Movimentações"**: Exibe histórico completo de todas as movimentações de estoque com data, localização, produto, tipo e quantidade
- **Busca combinada**: Dois campos de busca independentes - "Buscar localização..." e "Buscar por referência...", que trabalham em conjunto para filtrar a grade do armazém
- **Nomes de abas atualizados**: "Mapa" em vez de "Visualização em Grade", "Grade" em vez de "Tabela de Estoque"
- **Ordem lógica das abas**: Mapa → Grade → Movimentações → Configurações

### Funcionalidades
- **Filtro refinado**: A busca por referência agora procura pelo campo "ref" (referência do produto) em vez do nome
- **Atualização automática**: A aba de movimentações é atualizada automaticamente quando selecionada
- **Feedback visual**: Movimentações de entrada são destacadas em verde e saídas em vermelho
- **Atualização em tempo real**: A filtragem ocorre conforme o usuário digita em qualquer campo de busca

### Correções
- Corrigido erro de banco de dados somente leitura
- Corrigidos erros de sintaxe no JavaScript que impediam o funcionamento das abas
- Removida duplicação de elementos na definição de variáveis do JavaScript

## 📈 API Endpoints

- `GET /` - Interface principal
- `GET /api/stock` - Lista estoque
- `GET /api/movements` - Lista histórico de movimentações
- `POST /api/movement` - Registra movimentação
- `GET /api/export/csv` - Exporta CSV
- `GET /api/products` - Lista produtos
- `GET /api/locations` - Lista localizações

## 🐛 Troubleshooting

- Verifique se as portas 8090 e 5000 estão livres
- Execute `docker-compose logs` para ver logs (produção)
- Reinicie com `docker-compose restart`
- Verifique se os arquivos CSV estão no formato correto
- Para desenvolvimento local: acesse em http://localhost:5000

## 📄 Licença

MIT License