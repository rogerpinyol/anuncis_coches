from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Usuario, Cotxe, CotxeHybrid, CotxeElectric, Transaccion
from mongo_db import MongoDB
from config import Config
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'your_secret_key'

# Verify database URL before initializing
print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Initialize SQLAlchemy
db.init_app(app)

# Initialize MongoDB
mongo = MongoDB(app)

# Helper per a migrar la data existent de JSON a la base de dades
def migrate_json_to_db():
    try:
        with open("data.json", "r", encoding="utf-8") as file:
            anuncios = json.load(file)
            
            # Crear demo user si no existeix
            demo_user = Usuario.query.filter_by(email="demo@example.com").first()
            if not demo_user:
                demo_user = Usuario(
                    nom="Usuario Demo",
                    email="demo@example.com",
                    password="password",  # Això ha d'estar encriptat, com es de prova ho deixo així
                    tipus="Venedor"
                )
                db.session.add(demo_user)
                db.session.commit()
            
            # Afegir cotxes a MariaDB
            for anuncio in anuncios:
                # Check si el cotxe ja existeix
                existing = Cotxe.query.filter_by(
                    marca=anuncio["marca"],
                    model=anuncio["modelo"],
                    any=anuncio["any"]
                ).first()
                
                if not existing:
                    # Crear tipus de cotxe adequat
                    if anuncio["tipo"] == "electrico":
                        car_type = "Electric"
                        car_class = CotxeElectric
                    elif anuncio["tipo"] == "hibrido":
                        car_type = "Híbrid"
                        car_class = CotxeHybrid
                    else:
                        car_type = "Gasolina"
                        car_class = Cotxe
                        
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
            
            # Afegir preu inicial a MongoDB
            for car in Cotxe.query.all():
                mongo.add_preu_history(car.id, float(car.preu))
                
    except FileNotFoundError:
        pass

# Routes
@app.route("/")
def index():
    return render_template("index.html")  # Muestra la pagina principal

@app.route("/anuncios")
def anuncios():
    # Obtenir tots els cotxes de la database
    cotxes = Cotxe.query.all()
    return render_template("anuncios.html", anuncios=cotxes)

@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    if request.method == "POST":
        # Ens farà falta autenticació, de moment usarem un usuari demo
        usuario = Usuario.query.first()
        
        tipo = request.form["tipo"]
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        precio = float(request.form["precio"])
        any = int(request.form["any"])
        en_oferta = "oferta" in request.form
        
        if en_oferta:
            precio_original = precio
            precio *= 0.79  # 21% descompte
        
        # Crear el cotxe segons el tipus
        if tipo == "electrico":
            cotxe = CotxeElectric(
                marca=marca,
                model=modelo,
                preu=precio,
                any=any,
                tipus="Electric",
                venedor_id=usuario.id if usuario else None
            )
        elif tipo == "hibrido":
            cotxe = CotxeHybrid(
                marca=marca,
                model=modelo,
                preu=precio,
                any=any,
                tipus="Híbrid",
                venedor_id=usuario.id if usuario else None
            )
        else:
            cotxe = Cotxe(
                marca=marca,
                model=modelo,
                preu=precio,
                any=any,
                tipus="Gasolina",
                venedor_id=usuario.id if usuario else None
            )
        
        db.session.add(cotxe)
        db.session.commit()
        
        # Afegir a l'històric de preus a MongoDB
        mongo.add_preu_history(cotxe.id, float(cotxe.preu))
            
        return redirect(url_for("anuncios"))
        
    return render_template("publicar.html")

@app.route("/buscar", methods=["GET"])
def buscar():
    marca = request.args.get("marca", "").lower()
    modelo = request.args.get("modelo", "").lower()
    precio_max = request.args.get("precio")
    anyo = request.args.get("any")
    
    # Construir la query
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

# MongoDB functionality routes
@app.route("/favorito/add/<int:cotxe_id>", methods=["POST"])
def add_favorito(cotxe_id):
    # Això requeriria autenticació d'usuari
    usuario_id = 1  # Demo user de moment
    
    mongo.add_favorit(usuario_id, cotxe_id)
    flash("Coche añadido a favoritos")
    
    return redirect(url_for("anuncios"))

@app.route("/favoritos")
def ver_favoritos():
    # Això requeriria autenticació d'usuari
    usuario_id = 1  # Demo user
    
    favoritos_ids = mongo.get_favorits(usuario_id)
    favoritos = Cotxe.query.filter(Cotxe.id.in_(favoritos_ids)).all() if favoritos_ids else []
    
    return render_template("favoritos.html", anuncios=favoritos)

@app.route("/oferta/<int:cotxe_id>", methods=["GET", "POST"])
def hacer_oferta(cotxe_id):
    cotxe = Cotxe.query.get_or_404(cotxe_id)
    
    if request.method == "POST":
        # Això requeriria autenticació d'usuari
        usuario_id = 1  # Demo user 
        oferta = float(request.form["oferta"])
        
        mongo.add_oferta(cotxe_id, usuario_id, oferta)
        flash("Oferta enviada correctamente")
        
        return redirect(url_for("anuncios"))
    
    return render_template("hacer_oferta.html", cotxe=cotxe)

@app.route("/ofertas/<int:cotxe_id>")
def ver_ofertas(cotxe_id):
    cotxe = Cotxe.query.get_or_404(cotxe_id)
    ofertas = mongo.get_ofertes(cotxe_id)
    
    # Obtenir user info per cada oferta
    for oferta in ofertas:
        usuario = Usuario.query.get(oferta['usuari_id'])
        oferta['nombre_usuario'] = usuario.nom if usuario else "Usuario desconocido"
    
    return render_template("ofertas.html", cotxe=cotxe, ofertas=ofertas)

@app.route("/aceptar-oferta/<int:cotxe_id>/<int:usuari_id>", methods=["POST"])
def aceptar_oferta(cotxe_id, usuari_id):
    cotxe = Cotxe.query.get_or_404(cotxe_id)
    ofertas = mongo.get_ofertes(cotxe_id)
    
    # Buscar oferta concreta
    oferta = next((o for o in ofertas if o['usuari_id'] == usuari_id), None)
    
    if oferta:
        # Update offer status
        mongo.update_oferta_status(cotxe_id, usuari_id, 'Acceptada')
        
        # Crear transacció
        transaccion = Transaccion(
            comprador_id=usuari_id,
            cotxe_id=cotxe_id,
            preu_final=oferta['preu_ofert']
        )
        db.session.add(transaccion)
        db.session.commit()
        
        flash("Oferta aceptada y venta completada")
    else:
        flash("Oferta no encontrada")
    
    return redirect(url_for("ver_ofertas", cotxe_id=cotxe_id))

@app.route("/historial-precios/<int:cotxe_id>")
def historial_precios(cotxe_id):
    cotxe = Cotxe.query.get_or_404(cotxe_id)
    historial = mongo.get_preu_history(cotxe_id)
    
    return render_template("historial_precios.html", cotxe=cotxe, historial=historial)

@app.route("/comentarios/<int:cotxe_id>", methods=["GET", "POST"])
def comentarios(cotxe_id):
    cotxe = Cotxe.query.get_or_404(cotxe_id)
    
    if request.method == "POST":

        usuario_id = 1  # Demo user
        comentario = request.form["comentario"]
        
        mongo.add_comentari(cotxe_id, usuario_id, comentario)
        flash("Comentario añadido correctamente")
        
    comentarios = mongo.get_comentaris(cotxe_id)
    
    # Obtindre informació de l'usuari per a cada comentari
    for comentario in comentarios:
        usuario = Usuario.query.get(comentario['usuari_id'])
        comentario['nombre_usuario'] = usuario.nom if usuario else "Usuario desconocido"
    
    return render_template("comentarios.html", cotxe=cotxe, comentarios=comentarios)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        migrate_json_to_db()
    app.run(debug=True)
