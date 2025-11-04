import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

# --- Configuración Inicial ---
app = Flask(__name__, template_folder='template')

# --- Configuración de la Base de Datos ---
# CORRECCIÓN: Usamos la variable de entorno DATABASE_URL si existe,
# si no, usamos directamente la cadena de conexión que proporcionaste.
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://criadero_guerrero_user:CqfpUAb2qmAZkZLRI1s73pJDAf15gipd@dpg-d4572k6uk2gs73ak8mpg-a.virginia-postgres.render.com/criadero_guerrero"
)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modelo de la Base de Datos ---
class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    cliente = db.Column(db.String(150), nullable=False)
    familia = db.Column(db.String(100))
    especie = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    total_venta = db.Column(db.Float, nullable=False)
    notas = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat(),
            'cliente': self.cliente,
            'familia': self.familia,
            'especie': self.especie,
            'cantidad': self.cantidad,
            'precio': self.precio,
            'total': self.total_venta,
            'notas': self.notas
        }

# --- Rutas de la Aplicación (Endpoints) ---

@app.route('/')
def index():
    """Muestra la página principal (el formulario de registro)."""
    return render_template('index.html')

@app.route('/agregar', methods=['POST'])
def agregar_venta():
    """Recibe los datos de una nueva venta y los guarda en la base de datos."""
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['fecha', 'cliente', 'especie', 'cantidad', 'precio', 'total']):
            return jsonify({'success': False, 'error': 'Faltan datos requeridos'}), 400

        nueva_venta = Venta(
            fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date(),
            cliente=data['cliente'],
            familia=data.get('familia'),
            especie=data['especie'],
            cantidad=float(data['cantidad']),
            precio=float(data['precio']),
            total_venta=float(data['total']),
            notas=data.get('notas')
        )
        
        db.session.add(nueva_venta)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Venta registrada con éxito'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al agregar venta: {e}")
        return jsonify({'success': False, 'error': 'Ocurrió un error en el servidor.'}), 500

@app.route('/reporte')
def reporte():
    """Consulta todas las ventas en la BD y las envía a la página de reporte."""
    try:
        ventas_query = Venta.query.order_by(Venta.fecha.desc(), Venta.id.desc()).all()
        ventas_json = json.dumps([venta.to_dict() for venta in ventas_query])
        
        # CORRECCIÓN: 'render_template' busca en la carpeta 'template' por defecto.
        # No es necesario poner './'.
        return render_template('ventas.html', ventas_json=ventas_json)
    except Exception as e:
        app.logger.error(f"Error al obtener reporte: {e}")
        
        # CORRECCIÓN: 'render_template' busca en la carpeta 'template' por defecto.
        return render_template('ventas.html', ventas_json="[]", error="No se pudo conectar a la base de datos.")

# --- Inicialización del Servidor ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # NOTA: El host '0.0.0.0' es correcto para contenedores/servidores.
    app.run(host='0.0.0.0', port=5000, debug=True)
