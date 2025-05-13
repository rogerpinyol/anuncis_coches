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
    
    # Relacions
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
    autonomia = db.Column(db.Integer, nullable=True)  # Només per a cotxes elèctrics/híbrids
    
    # "Discriminator" column que permet l'herència al servir com a base
    type = db.Column(db.String(20))
    
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'cotxe'
    }
    
    # Relacions
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