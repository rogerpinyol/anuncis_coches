from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuaris'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))  # Increased from 100 to 255 to accommodate hashed passwords
    tipus = db.Column(db.Enum('Comprador', 'Venedor', name='tipus_usuari'))
    
    # Relacions
    coches_vendidos = db.relationship('Cotxe', backref='vendedor', lazy=True)
    compras = db.relationship('Transaccion', backref='comprador', lazy=True)

class Cotxe(db.Model):
    __tablename__ = 'cotxes'
    
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(100))
    model = db.Column(db.String(100))
    preu = db.Column(db.Numeric(10, 2))
    any = db.Column(db.Integer)
    tipus = db.Column(db.Enum('Gasolina', 'Diesel', 'Electric', 'Híbrid', name='tipus_cotxe'))
    venedor_id = db.Column(db.Integer, db.ForeignKey('usuaris.id'))
    
    # New common fields
    eficiencia_combustible = db.Column(db.Float, nullable=True)  # L/100km
    emisiones_co2 = db.Column(db.Float, nullable=True)  # g/km
    
    # Fields for electric/hybrid vehicles
    capacidad_bateria = db.Column(db.Float, nullable=True)  # kWh
    tiempo_carga = db.Column(db.Integer, nullable=True)  # minutes
    salud_bateria = db.Column(db.Integer, nullable=True)  # percentage
    
    # Discriminator column
    type = db.Column(db.String(20))
    
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'cotxe'
    }
    
    # Relations
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
    data_venda = db.Column(db.DateTime, default=datetime.now)