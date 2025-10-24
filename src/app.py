from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import os
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.config['DATABASE'] = os.getenv('DATABASE_URL', 'sqlite:///warehouse.db').replace('sqlite:///', '')

# Se o caminho for apenas um nome de arquivo, coloque no diretório data
if '/' not in app.config['DATABASE'] or app.config['DATABASE'].startswith('warehouse.db'):
    app.config['DATABASE'] = 'data/warehouse.db'

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

@app.route('/api/movement', methods=['POST'])
def register_movement():
    data = request.json or {}
    location_code = data.get('location')  # Agora é o código (A001C, etc.)
    product_ref = data.get('product')
    quantity = data.get('quantity')
    movement_type = data.get('type')  # 'entry' or 'exit'
    
    if not all([location_code, product_ref, quantity, movement_type]):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    try:
        quantity = int(quantity or 0)
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

@app.route('/api/products', methods=['POST'])
def add_product():
    """Adicionar novo produto"""
    data = request.json or {}
    ref = data.get('ref')
    name = data.get('name')
    
    if not ref or not name:
        return jsonify({'error': 'Referência e nome são obrigatórios'}), 400
    
    conn = get_db_connection()
    
    try:
        # Verificar se o produto já existe
        existing = conn.execute(
            'SELECT id FROM products WHERE ref = ?', (ref,)
        ).fetchone()
        
        if existing:
            return jsonify({'error': 'Produto com esta referência já existe'}), 400
        
        # Inserir novo produto
        conn.execute(
            'INSERT INTO products (ref, name) VALUES (?, ?)',
            (ref, name)
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Produto adicionado com sucesso'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/locations', methods=['POST'])
def add_location():
    """Adicionar nova localização"""
    data = request.json or {}
    cod = data.get('cod')
    local = data.get('local')
    armazem = data.get('armazem', 'LOG')
    
    if not cod or not local:
        return jsonify({'error': 'Código e localização são obrigatórios'}), 400
    
    conn = get_db_connection()
    
    try:
        # Verificar se a localização já existe
        existing_by_cod = conn.execute(
            'SELECT id FROM locations WHERE cod = ?', (cod,)
        ).fetchone()
        
        existing_by_local = conn.execute(
            'SELECT id FROM locations WHERE local = ?', (local,)
        ).fetchone()
        
        if existing_by_cod or existing_by_local:
            return jsonify({'error': 'Localização com este código ou local já existe'}), 400
        
        # Inserir nova localização
        conn.execute(
            'INSERT INTO locations (cod, local, armazem) VALUES (?, ?, ?)',
            (cod, local, armazem)
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Localização adicionada com sucesso'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

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

@app.route('/api/import/status')
def import_status():
    """Verificar status dos arquivos de importação"""
    # Use the correct path based on the environment
    database_url = os.getenv('DATABASE_URL', '')
    import_dir = '/app/data/import' if database_url.startswith('sqlite:////app/') else 'data/import'
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