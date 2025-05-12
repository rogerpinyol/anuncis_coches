Define SQLAlchemy Models for MariaDB

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuaris'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    tipus = db.Column(db.Enum('Comprador', 'Venedor', name='tipus_usuari'))
    
    # Relationships
    coches_vendidos = db.relationship('Cotxe', backref='vendedor', lazy=True)
    compras = db.relationship('Transaccion', backref='comprador', lazy=True)

class Cotxe(db.Model):
    __tablename__ = 'cotxes'
    
    id = db.Column(db.Integer, primary_key=True)
    venedor_id = db.Column(db.Integer, db.ForeignKey('usuaris.id'))
    marca = db.Column(db.String(50))
    model = db.Column(db.String(50))
    any = db.Column(db.Integer)
    preu = db.Column(db.Numeric(10, 2))
    tipus = db.Column(db.Enum('Gasolina', 'Diesel', 'Electric', 'Híbrid', name='tipus_cotxe'))
    autonomia = db.Column(db.Integer, nullable=True)  # Only for electric/hybrid
    
    # Discriminator column for inheritance
    type = db.Column(db.String(20))
    
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'cotxe'
    }
    
    # Relationship
    transacciones = db.relationship('Transaccion', backref='cotxe', lazy=True)
    
    def mostrar_informacion(self):
        return "⛽ Hay que contaminar menos!!!"

class CotxeHybrid(Cotxe):
    __mapper_args__ = {
        'polymorphic_identity': 'hibrido'
    }
    
    def mostrar_informacion(self):
        return "⚡⛽ ¡Ahorra combustible!"

class CotxeElectric(Cotxe):
    __mapper_args__ = {
        'polymorphic_identity': 'electrico'
    }
    
    def mostrar_informacion(self):
        return "⚡ Cero emisiones!"

class Transaccion(db.Model):
    __tablename__ = 'transaccions'
    
    id = db.Column(db.Integer, primary_key=True)
    comprador_id = db.Column(db.Integer, db.ForeignKey('usuaris.id'))
    cotxe_id = db.Column(db.Integer, db.ForeignKey('cotxes.id'))
    preu_final = db.Column(db.Numeric(10, 2))
    data_venda = db.Column(db.DateTime, default=datetime.utcnow)
```

Set Up MongoDB Connection and Helpers
```python
from pymongo import MongoClient
from bson.objectid import ObjectId

class MongoDB:
    def __init__(self, app=None):
        self.client = None
        self.db = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        mongo_uri = app.config.get('MONGO_URI')
        mongo_db = app.config.get('MONGO_DB')
        
        self.client = MongoClient(mongo_uri)
        self.db = self.client[mongo_db]
    
    # Comentaris collection methods
    def add_comentari(self, cotxe_id, usuari_id, comentari):
        comentaris_col = self.db.comentaris
        
        # Check if document for this car exists
        doc = comentaris_col.find_one({'cotxe_id': cotxe_id})
        
        if doc:
            # Add comment to existing document
            comentaris_col.update_one(
                {'cotxe_id': cotxe_id},
                {'$push': {'resenyes': {
                    'usuari_id': usuari_id,
                    'comentari': comentari,
                    'data': datetime.utcnow()
                }}}
            )
        else:
            # Create new document
            comentaris_col.insert_one({
                'cotxe_id': cotxe_id,
                'resenyes': [{
                    'usuari_id': usuari_id,
                    'comentari': comentari,
                    'data': datetime.utcnow()
                }]
            })
    
    def get_comentaris(self, cotxe_id):
        doc = self.db.comentaris.find_one({'cotxe_id': cotxe_id})
        return doc['resenyes'] if doc else []
    
    # Similar methods for other collections...
    
    # Favorits collection methods
    def add_favorit(self, usuari_id, cotxe_id):
        favorits_col = self.db.favorits
        
        # Check if user already has favorites
        doc = favorits_col.find_one({'usuari_id': usuari_id})
        
        if doc:
            # Add to existing favorites if not already present
            if cotxe_id not in doc['cotxes_guardats']:
                favorits_col.update_one(
                    {'usuari_id': usuari_id},
                    {'$push': {'cotxes_guardats': cotxe_id}}
                )
        else:
            # Create new document
            favorits_col.insert_one({
                'usuari_id': usuari_id,
                'cotxes_guardats': [cotxe_id]
            })
    
    # Additional methods for historial_preus and ofertes collections
```
Update the Main Application
```python
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, Usuario, Cotxe, CotxeHybrid, CotxeElectric, Transaccion
from mongo_db import MongoDB
import json

app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy
db.init_app(app)

# Initialize MongoDB
mongo = MongoDB(app)

# Create all tables
@app.before_first_request
def create_tables():
    db.create_all()

# Utility to migrate existing data from JSON to databases
def migrate_json_to_db():
    try:
        with open("data.json", "r", encoding="utf-8") as file:
            anuncios = json.load(file)
            
            # Create demo user if not exists
            demo_user = Usuario.query.filter_by(email="demo@example.com").first()
            if not demo_user:
                demo_user = Usuario(
                    nom="Demo User",
                    email="demo@example.com",
                    password="password",  # In production, hash this!
                    tipus="Venedor"
                )
                db.session.add(demo_user)
                db.session.commit()
            
            # Add cars to MariaDB
            for anuncio in anuncios:
                # Check if car already exists
                existing = Cotxe.query.filter_by(
                    marca=anuncio["marca"],
                    model=anuncio["modelo"],
                    any=anuncio["any"]
                ).first()
                
                if not existing:
                    # Create appropriate car type
                    if anuncio["tipo"] == "electrico":
                        new_car = CotxeElectric(
                            marca=anuncio["marca"],
                            model=anuncio["modelo"],
                            preu=anuncio["precio"],
                            any=anuncio["any"],
                            venedor_id=demo_user.id
                        )
                    elif anuncio["tipo"] == "hibrido":
                        new_car = CotxeHybrid(
                            marca=anuncio["marca"],
                            model=anuncio["modelo"],
                            preu=anuncio["precio"],
                            any=anuncio["any"],
                            venedor_id=demo_user.id
                        )
                    else:
                        new_car = Cotxe(
                            marca=anuncio["marca"],
                            model=anuncio["modelo"],
                            preu=anuncio["precio"],
                            any=anuncio["any"],
                            tipus="Gasolina",
                            venedor_id=demo_user.id
                        )
                    
                    db.session.add(new_car)
            
            db.session.commit()
            
    except FileNotFoundError:
        pass

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/anuncios")
def anuncios():
    # Get all cars from database
    coches = Cotxe.query.all()
    return render_template("anuncios.html", anuncios=coches)

@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    if request.method == "POST":
        # We'll need user authentication, but for now use a demo user
        usuario = Usuario.query.first()
        
        tipo = request.form["tipo"]
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        precio = float(request.form["precio"])
        any = int(request.form["any"])
        en_oferta = "oferta" in request.form
        
        if en_oferta:
            precio *= 0.79  # 21% discount
        
        # Create car based on type
        if tipo == "electrico":
            coche = CotxeElectric(
                marca=marca,
                model=modelo,
                preu=precio,
                any=any,
                tipus="Electric",
                venedor_id=usuario.id if usuario else None
            )
        elif tipo == "hibrido":
            coche = CotxeHybrid(
                marca=marca,
                model=modelo,
                preu=precio,
                any=any,
                tipus="Híbrid",
                venedor_id=usuario.id if usuario else None
            )
        else:
            coche = Cotxe(
                marca=marca,
                model=modelo,
                preu=precio,
                any=any,
                tipus="Gasolina",
                venedor_id=usuario.id if usuario else None
            )
        
        db.session.add(coche)
        db.session.commit()
        
        # If the car is on sale, add to price history
        if en_oferta:
            mongo.db.historial_preus.update_one(
                {'cotxe_id': coche.id},
                {'$push': {'preus': {
                    'data': datetime.utcnow(),
                    'preu': precio
                }}},
                upsert=True
            )
            
        return redirect(url_for("anuncios"))
        
    return render_template("publicar.html")

@app.route("/buscar", methods=["GET"])
def buscar():
    marca = request.args.get("marca", "").lower()
    modelo = request.args.get("modelo", "").lower()
    precio_max = request.args.get("precio")
    anyo = request.args.get("any")
    
    # Build the query
    query = Cotxe.query
    
    if marca:
        query = query.filter(Cotxe.marca.ilike(f"%{marca}%"))
    if modelo:
        query = query.filter(Cotxe.model.ilike(f"%{modelo}%"))
    if precio_max:
        query = query.filter(Cotxe.preu <= float(precio_max))
    if anyo:
        query = query.filter(Cotxe.any == int(anyo))
    
    resultados = query.all()
    
    return render_template("buscar.html", anuncios=resultados)

# More routes for MongoDB functionality
@app.route("/favoritos", methods=["POST"])
def add_favorito():
    # This would require user authentication
    usuario_id = 1  # Placeholder
    cotxe_id = int(request.form["cotxe_id"])
    
    mongo.add_favorit(usuario_id, cotxe_id)
    
    return redirect(url_for("anuncios"))

@app.route("/comentarios/<int:cotxe_id>", methods=["GET", "POST"])
def comentarios(cotxe_id):
    if request.method == "POST":
        # This would require user authentication
        usuario_id = 1  # Placeholder
        comentario = request.form["comentario"]
        
        mongo.add_comentari(cotxe_id, usuario_id, comentario)
        
    comentarios = mongo.get_comentaris(cotxe_id)
    return render_template("comentarios.html", comentarios=comentarios, cotxe_id=cotxe_id)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        migrate_json_to_db()
    app.run(debug=True)
```
Create a Migration Script JSON -> Databases

```python
from app import app, db, mongo
from models import Usuario, Cotxe, CotxeHybrid, CotxeElectric
import json
from datetime import datetime

def migrate_json_to_databases():
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Create a demo user
            demo_user = Usuario.query.filter_by(email="demo@example.com").first()
            if not demo_user:
                demo_user = Usuario(
                    nom="Demo User",
                    email="demo@example.com",
                    password="password",  # Should be hashed in production
                    tipus="Venedor"
                )
                db.session.add(demo_user)
                db.session.commit()
            
            # Load JSON data
            with open("data.json", "r", encoding="utf-8") as file:
                anuncios = json.load(file)
            
            # Migrate to MariaDB
            for anuncio in anuncios:
                # Map car type
                if anuncio["tipo"] == "electrico":
                    car_type = "Electric"
                    car_class = CotxeElectric
                elif anuncio["tipo"] == "hibrido":
                    car_type = "Híbrid"
                    car_class = CotxeHybrid
                else:
                    car_type = "Gasolina"
                    car_class = Cotxe
                
                # Check if car already exists
                existing = Cotxe.query.filter_by(
                    marca=anuncio["marca"],
                    model=anuncio["modelo"],
                    any=anuncio["any"]
                ).first()
                
                if not existing:
                    # Create the car
                    new_car = car_class(
                        marca=anuncio["marca"],
                        model=anuncio["modelo"],
                        preu=anuncio["precio"],
                        any=anuncio["any"],
                        tipus=car_type,
                        venedor_id=demo_user.id
                    )
                    db.session.add(new_car)
            
            db.session.commit()
            
            # Add price history to MongoDB for each car
            for car in Cotxe.query.all():
                mongo.db.historial_preus.insert_one({
                    'cotxe_id': car.id,
                    'preus': [{
                        'data': datetime.utcnow(),
                        'preu': float(car.preu)
                    }]
                })
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_json_to_databases()
```