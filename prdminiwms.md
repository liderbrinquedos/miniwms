# Documentação do Mini-WMS com Docker - Estrutura Atualizada

Vou atualizar a estrutura para usar o novo formato de localizações com COD, LOCAL, ARMAZEM e incluir as melhorias implementadas recentemente.

## Estrutura do Projeto Atualizada

```
mini-wms/
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
├── entrypoint.sh
├── src/
│   ├── app.py
│   ├── database.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── style.css
├── data/
│   ├── import/
│   │   ├── locations.csv
│   │   └── products.csv
│   └── warehouse.db (gerado automaticamente)
├── requirements.txt
└── README.md
```

## 1. src/database.py Atualizado

```python
import sqlite3
import os
import csv
from datetime import datetime

def init_database():
    db_path = os.getenv('DATABASE_URL', 'sqlite:///warehouse.db').replace('sqlite:///', '')
    
    # Garantir que o diretório existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabela de produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ref TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de localizações (estrutura atualizada)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cod TEXT UNIQUE NOT NULL,
            local TEXT NOT NULL,
            armazem TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de estoque
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            UNIQUE(location_id, product_id)
        )
    ''')
    
    # Tabela de movimentações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            type TEXT NOT NULL, -- 'entry' or 'exit'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Importar dados dos arquivos CSV
    import_from_csv(cursor)
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso!")

def import_from_csv(cursor):
    base_path = '/app/data/import'
    
    # Importar produtos
    products_csv = os.path.join(base_path, 'products.csv')
    if os.path.exists(products_csv):
        print("Importando produtos do CSV...")
        with open(products_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute(
                    'INSERT OR IGNORE INTO products (ref, name) VALUES (?, ?)',
                    (row['ref'], row['name'])
                )
        print(f"Produtos importados de {products_csv}")
    else:
        print(f"Arquivo {products_csv} não encontrado, usando dados padrão")
        insert_default_products(cursor)
    
    # Importar localizações (formato atualizado)
    locations_csv = os.path.join(base_path, 'locations.csv')
    if os.path.exists(locations_csv):
        print("Importando localizações do CSV...")
        with open(locations_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute(
                    'INSERT OR IGNORE INTO locations (cod, local, armazem) VALUES (?, ?, ?)',
                    (row['COD'], row['LOCAL'], row.get('ARMAZEM', 'LOG'))
                )
        print(f"Localizações importadas de {locations_csv}")
    else:
        print(f"Arquivo {locations_csv} não encontrado, usando dados padrão")
        insert_default_locations(cursor)

def insert_default_products(cursor):
    """Inserir produtos padrão se CSV não existir"""
    products = [
        ('P1001', 'CAR BOLA'),
        ('P1002', 'CAR CHORRO'),
        ('P1003', 'CAR TUCHO'),
        ('P1004', 'CAR MARGO'),
        ('P1005', 'CAR SETE'),
        ('P1006', 'CAR JOGO')
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO products (ref, name) VALUES (?, ?)',
        products
    )

def insert_default_locations(cursor):
    """Inserir localizações padrão se CSV não existir"""
    locations = [
        ('10000', 'A001C', 'LOG'),
        ('10001', 'A001D', 'LOG'),
        ('10002', 'A002C', 'LOG'),
        ('10003', 'A002D', 'LOG'),
        ('10004', 'A003C', 'LOG'),
        ('10005', 'A003D', 'LOG'),
        ('10006', 'A004A', 'LOG'),
        ('10007', 'A004B', 'LOG'),
        ('10008', 'A004C', 'LOG'),
        ('10009', 'A004D', 'LOG'),
        ('10010', 'B001A', 'LOG'),
        ('10011', 'B001B', 'LOG')
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO locations (cod, local, armazem) VALUES (?, ?, ?)',
        locations
    )

if __name__ == '__main__':
    init_database()
```

## 2. src/app.py Atualizado com Melhorias

```python
from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import os
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.config['DATABASE'] = os.getenv('DATABASE_URL', 'sqlite:///warehouse.db').replace('sqlite:///', '')

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products')
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY ref').fetchall()
    conn.close()
    return jsonify([dict(product) for product in products])

@app.route('/api/locations')
def get_locations():
    conn = get_db_connection()
    locations = conn.execute('SELECT * FROM locations ORDER BY local').fetchall()
    conn.close()
    return jsonify([dict(location) for location in locations])

@app.route('/api/stock')
def get_stock():
    conn = get_db_connection()
    stock = conn.execute('''
        SELECT l.local as location, l.cod as location_code, p.ref, p.name, s.quantity
        FROM stock s
        JOIN locations l ON s.location_id = l.id
        JOIN products p ON s.product_id = p.id
        ORDER BY l.local
    ''').fetchall()
    conn.close()
    return jsonify([dict(item) for item in stock])

@app.route('/api/movements')
def get_movements():
    conn = get_db_connection()
    movements = conn.execute('''
        SELECT m.created_at, l.local as location, p.ref, p.name, m.type, m.quantity
        FROM movements m
        JOIN locations l ON m.location_id = l.id
        JOIN products p ON m.product_id = p.id
        ORDER BY m.created_at DESC
        LIMIT 100
    ''').fetchall()
    conn.close()
    return jsonify([dict(movement) for movement in movements])

@app.route('/api/movement', methods=['POST'])
def register_movement():
    data = request.json
    location_code = data.get('location')  # Agora é o código (A001C, etc.)
    product_ref = data.get('product')
    quantity = data.get('quantity')
    movement_type = data.get('type')  # 'entry' or 'exit'
    
    if not all([location_code, product_ref, quantity, movement_type]):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'error': 'Quantidade deve ser positiva'}), 400
    except ValueError:
        return jsonify({'error': 'Quantidade inválida'}), 400
    
    conn = get_db_connection()
    
    try:
        # Obter IDs - agora buscando pelo campo 'local'
        location = conn.execute(
            'SELECT id, local FROM locations WHERE local = ?', (location_code,)
        ).fetchone()
        product = conn.execute(
            'SELECT id FROM products WHERE ref = ?', (product_ref,)
        ).fetchone()
        
        if not location:
            return jsonify({'error': 'Localização não encontrada'}), 404
        if not product:
            return jsonify({'error': 'Produto não encontrado'}), 404
        
        # Verificar estoque para saída
        if movement_type == 'exit':
            current_stock = conn.execute('''
                SELECT quantity FROM stock 
                WHERE location_id = ? AND product_id = ?
            ''', (location['id'], product['id'])).fetchone()
            
            if not current_stock or current_stock['quantity'] < quantity:
                return jsonify({'error': 'Estoque insuficiente'}), 400
        
        # Atualizar estoque
        if movement_type == 'entry':
            conn.execute('''
                INSERT INTO stock (location_id, product_id, quantity, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(location_id, product_id) 
                DO UPDATE SET quantity = quantity + excluded.quantity
            ''', (location['id'], product['id'], quantity))
        else:  # exit
            conn.execute('''
                UPDATE stock 
                SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP
                WHERE location_id = ? AND product_id = ?
            ''', (quantity, location['id'], product['id']))
        
        # Registrar movimentação
        conn.execute('''
            INSERT INTO movements (location_id, product_id, quantity, type)
            VALUES (?, ?, ?, ?)
        ''', (location['id'], product['id'], quantity, movement_type))
        
        # Remover estoque zerado
        conn.execute('DELETE FROM stock WHERE quantity <= 0')
        
        conn.commit()
        return jsonify({'success': True, 'location': location['local']})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/export/csv')
def export_csv():
    conn = get_db_connection()
    stock = conn.execute('''
        SELECT l.cod as codigo, l.local as localizacao, l.armazem, p.ref, p.name, s.quantity
        FROM stock s
        JOIN locations l ON s.location_id = l.id
        JOIN products p ON s.product_id = p.id
        ORDER BY l.local
    ''').fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Código', 'Localização', 'Armazém', 'Referência', 'Nome do Produto', 'Quantidade'])
    
    for item in stock:
        writer.writerow([
            item['codigo'], 
            item['localizacao'], 
            item['armazem'],
            item['ref'], 
            item['name'], 
            item['quantity']
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'stock_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/import/status')
def import_status():
    """Verificar status dos arquivos de importação"""
    import_dir = '/app/data/import'
    status = {
        'products_csv': os.path.exists(os.path.join(import_dir, 'products.csv')),
        'locations_csv': os.path.exists(os.path.join(import_dir, 'locations.csv'))
    }
    return jsonify(status)

if __name__ == '__main__':
    # Verificar se o banco existe, se não, criar
    if not os.path.exists(app.config['DATABASE']):
        from database import init_database
        init_database()
    
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
```

## 3. src/templates/index.html - Atualizações com Melhorias

No arquivo `src/templates/index.html`, foram implementadas as seguintes melhorias:

1. **Nova aba "Movimentações"**: Exibe o histórico completo de movimentações de estoque
2. **Busca combinada**: Dois campos de busca - localização e referência do produto
3. **Nomes atualizados de abas**: "Mapa", "Grade", "Movimentações", "Configurações"

### Atualização da interface:
- Nova rota `/api/movements` adicionada no backend
- Nova aba HTML para exibir movimentações
- Função JavaScript `renderMovements()` para carregar dados
- Event listener para atualizar a aba ao selecionar

### Atualização da busca:
- Campo adicional "Buscar por referência..."
- Nova lógica de filtragem combinada
- Atualização em tempo real conforme digita

```html
<!-- No HTML, adicionei os novos campos de busca -->
<div class="search-bar" style="display: flex; gap: 10px;">
    <input type="text" id="searchInput" placeholder="Buscar localização...">
    <input type="text" id="productSearchInput" placeholder="Buscar por referência...">
</div>

<!-- Atualizei as abas -->
<div class="tabs">
    <div class="tab active" data-tab="grid">Mapa</div>
    <div class="tab" data-tab="table">Grade</div>
    <div class="tab" data-tab="movements">Movimentações</div>
    <div class="tab" data-tab="config">Configurações</div>
</div>

<!-- Adicionei o conteúdo da nova aba -->
<div class="tab-content" id="movements-tab">
    <div class="table-container">
        <table id="movementsTable">
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Localização</th>
                    <th>Referência</th>
                    <th>Produto</th>
                    <th>Tipo</th>
                    <th>Quantidade</th>
                </tr>
            </thead>
            <tbody id="movementsTableBody">
                <!-- Preenchido dinamicamente -->
            </tbody>
        </table>
    </div>
</div>
```

```javascript
// Atualização da função filterLocations com busca combinada
function filterLocations() {
    const searchTerm = elements.searchInput.value.toLowerCase();
    const productSearchTerm = elements.productSearchInput.value.toLowerCase();
    
    document.querySelectorAll('.location').forEach(el => {
        const locationCode = el.dataset.location.toLowerCase();
        const locationRef = el.querySelector('.location-ref').textContent.toLowerCase();
        
        // Verificar se a localização ou o produto correspondem aos termos de busca
        const locationMatch = locationCode.includes(searchTerm) || searchTerm === '';
        const productMatch = locationRef.includes(productSearchTerm) || productSearchTerm === '';
        
        if (locationMatch && productMatch) {
            el.style.display = 'flex';
        } else {
            el.style.display = 'none';
        }
    });
}

// Nova função renderMovements
async function renderMovements() {
    try {
        const response = await fetch(`${API_BASE}/movements`);
        const movements = await response.json();
        
        elements.movementsTableBody.innerHTML = '';
        
        movements.forEach(movement => {
            const row = document.createElement('tr');
            
            // Formatar a data
            const date = new Date(movement.created_at);
            const formattedDate = date.toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            // Determinar classe para tipo de movimentação
            const typeClass = movement.type === 'entry' ? 'movement-entry' : 'movement-exit';
            const typeText = movement.type === 'entry' ? 'Entrada' : 'Saída';
            
            row.innerHTML = `
                <td>${formattedDate}</td>
                <td>${movement.location}</td>
                <td>${movement.ref}</td>
                <td>${movement.name}</td>
                <td class="${typeClass}">${typeText}</td>
                <td>${movement.quantity}</td>
            `;
            
            elements.movementsTableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Erro ao carregar movimentações:', error);
        showNotification('Erro ao carregar histórico de movimentações', 'error');
    }
}

// Atualização da função switchTab
function switchTab(tabName) {
    // Remover classe ativa das abas
    elements.tabs.forEach(tab => tab.classList.remove('active'));
    elements.tabContents.forEach(content => content.classList.remove('active'));
    
    // Adicionar classe ativa à aba selecionada
    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Carregar dados específicos da aba se necessário
    if (tabName === 'movements') {
        renderMovements();
    }
}
```

## 4. Arquivos CSV de Exemplo Atualizados

### data/import/products.csv
```csv
ref,name
P1001,CAR BOLA
P1002,CAR CHORRO
P1003,CAR TUCHO
P1004,CAR MARGO
P1005,CAR SETE
P1006,CAR JOGO
```

### data/import/locations.csv (NOVO FORMATO)
```csv
COD,LOCAL,ARMAZEM
10000,A001C,LOG
10001,A001D,LOG
10002,A002C,LOG
10003,A002D,LOG
10004,A003C,LOG
10005,A003D,LOG
10006,A004A,LOG
10007,A004B,LOG
10008,A004C,LOG
10009,A004D,LOG
10010,B001A,LOG
10011,B001B,LOG
```

## 5. Melhorias Implementadas

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

## 6. README.md Atualizado

```markdown
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
```

## Comandos para Execução

```bash
# Criar estrutura de diretórios
mkdir -p data/import

# Colocar seus arquivos CSV em data/import/ com o novo formato

# Produção (porta 8090)
docker-compose up -d

# Desenvolvimento (porta 8091)
docker-compose -f docker-compose.dev.yml up --build

# Parar
docker-compose down

# Ver logs
docker-compose logs -f web

# Backup do banco
docker cp mini-wms_web_1:/app/data/warehouse.db ./backup.db

# Ver status da importação
curl http://localhost:8090/api/import/status
```

## Principais Mudanças

1. **Estrutura de Localizações**: 
   - `COD` (código único: 10000, 10001, etc.)
   - `LOCAL` (código da localização: A001C, A001D, etc.)
   - `ARMAZEM` (nome do armazém: LOG)

2. **API Adaptada**: 
   - Busca por localização agora usa o campo `local`
   - Exportação CSV inclui todos os campos novos

3. **Novas funcionalidades implementadas**:
   - Nova aba "Movimentações" com histórico completo
   - Busca combinada por localização e referência do produto
   - Nomes atualizados de abas
   - Melhor experiência do usuário

4. **Fallback**: 
   - Dados padrão atualizados com a nova estrutura
   - Sistema funciona mesmo sem arquivos CSV

A aplicação agora está completamente adaptada para a nova estrutura de localizações e inclui todas as melhorias implementadas recentemente, mantendo toda a funcionalidade anterior.