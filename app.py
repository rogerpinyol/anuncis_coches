from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_migrate import Migrate
from models import db, Usuario, Cotxe, CotxeHybrid, CotxeElectric, Transaccion
from mongo_db import MongoDB
from config import Config
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from auth import auth, login_required
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'no_la_canviare_xd'

# Verify database URL before initializing
print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize MongoDB
mongo = MongoDB(app)

# Register the auth blueprint
app.register_blueprint(auth, url_prefix='/auth')

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
@login_required
def publicar():
    if request.method == "POST":
        tipo = request.form["tipo"]
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        precio = request.form["precio"]
        any = request.form["any"]
        
        # Get environmental impact data
        eficiencia = request.form.get("eficiencia_combustible")
        emisiones = request.form.get("emisiones_co2")
        
        # Convert to proper types or None if empty
        eficiencia = float(eficiencia) if eficiencia else None
        emisiones = float(emisiones) if emisiones else None
        
        # Create the appropriate type of car
        if tipo == "electrico":
            # Get battery data
            capacidad = request.form.get("capacidad_bateria")
            tiempo_carga = request.form.get("tiempo_carga")
            salud_bateria = request.form.get("salud_bateria")
            
            # Convert to proper types or None if empty
            capacidad = float(capacidad) if capacidad else None
            tiempo_carga = int(tiempo_carga) if tiempo_carga else None
            salud_bateria = int(salud_bateria) if salud_bateria else None
            
            coche = CotxeElectric(
                marca=marca,
                model=modelo,
                preu=precio,
                any=any,
                tipus="Electric",
                venedor_id=session["user_id"],
                eficiencia_combustible=eficiencia,
                emisiones_co2=emisiones,
                capacidad_bateria=capacidad,
                tiempo_carga=tiempo_carga,
                salud_bateria=salud_bateria
            )
        elif tipo == "hibrido":
            # Get battery data
            capacidad = request.form.get("capacidad_bateria")
            tiempo_carga = request.form.get("tiempo_carga")
            salud_bateria = request.form.get("salud_bateria")
            combustible_tipo = request.form.get("combustible_tipo", "Gasolina")
            
            # Convert to proper types or None if empty
            capacidad = float(capacidad) if capacidad else None
            tiempo_carga = int(tiempo_carga) if tiempo_carga else None
            salud_bateria = int(salud_bateria) if salud_bateria else None
            
            coche = CotxeHybrid(
                marca=marca,
                model=modelo,
                preu=precio,
                any=any,
                tipus="Híbrid",
                venedor_id=session["user_id"],
                eficiencia_combustible=eficiencia,
                emisiones_co2=emisiones,
                capacidad_bateria=capacidad,
                tiempo_carga=tiempo_carga,
                salud_bateria=salud_bateria
            )
        else:  # normal (gasolina/diesel)
            combustible_tipo = request.form.get("combustible_tipo", "Gasolina")
            coche = Cotxe(
                marca=marca,
                model=modelo,
                preu=precio,
                any=any,
                tipus=combustible_tipo,
                venedor_id=session["user_id"],
                eficiencia_combustible=eficiencia,
                emisiones_co2=emisiones
            )
        
        db.session.add(coche)
        db.session.commit()
        
        # Add initial price to history
        mongo.add_preu_history(coche.id, float(precio))
        
        flash("Anuncio publicado correctamente")
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

@app.route("/coche/<int:cotxe_id>")
def detalle_coche(cotxe_id):
    cotxe = Cotxe.query.get_or_404(cotxe_id)
    
    # Get offers with user information
    ofertas = mongo.get_ofertes(cotxe_id)
    for oferta in ofertas:
        usuario = Usuario.query.get(oferta['usuari_id'])
        oferta['nombre_usuario'] = usuario.nom if usuario else "Usuario desconocido"
        
        # Format date
        if 'data' in oferta and oferta['data']:
            # Handle string dates or datetime objects
            if isinstance(oferta['data'], str):
                try:
                    date_obj = datetime.fromisoformat(oferta['data'].replace('Z', '+00:00'))
                    oferta['data'] = date_obj.strftime("%d/%m/%Y %H:%M")
                except ValueError:
                    # If date format is not ISO
                    pass
            else:
                oferta['data'] = oferta['data'].strftime("%d/%m/%Y %H:%M")
    
    # Get comments with user information
    comentarios = mongo.get_comentaris(cotxe_id)
    for comentario in comentarios:
        usuario = Usuario.query.get(comentario['usuari_id'])
        comentario['nombre_usuario'] = usuario.nom if usuario else "Usuario desconocido"
        
        # Format date
        if 'data' in comentario and comentario['data']:
            # Handle string dates or datetime objects
            if isinstance(comentario['data'], str):
                try:
                    date_obj = datetime.fromisoformat(comentario['data'].replace('Z', '+00:00'))
                    comentario['data'] = date_obj.strftime("%d/%m/%Y %H:%M") 
                except ValueError:
                    # If date format is not ISO
                    pass
            else:
                comentario['data'] = comentario['data'].strftime("%d/%m/%Y %H:%M")
    
    # Add this to pass the API key to the template
    api_key = os.getenv('OPENCHARGE_API_KEY')
    
    return render_template("detalle_coche.html", 
                         cotxe=cotxe,
                         ofertas=ofertas,
                         comentarios=comentarios,
                         api_key=api_key)

# MongoDB functionality routes
@app.route("/favorito/add/<int:cotxe_id>", methods=["POST"])
@login_required
def add_favorito(cotxe_id):
    usuario_id = session['user_id']  # Get logged in user's ID
    
    mongo.add_favorit(usuario_id, cotxe_id)
    flash("Coche añadido a favoritos")
    
    return redirect(url_for("anuncios"))

@app.route("/favoritos")
@login_required
def ver_favoritos():
    usuario_id = session['user_id']  # Get logged in user's ID
    
    favoritos_ids = mongo.get_favorits(usuario_id)
    favoritos = Cotxe.query.filter(Cotxe.id.in_(favoritos_ids)).all() if favoritos_ids else []
    
    return render_template("favoritos.html", anuncios=favoritos)

@app.route("/oferta/<int:cotxe_id>", methods=["GET", "POST"])
@login_required
def hacer_oferta(cotxe_id):
    cotxe = Cotxe.query.get_or_404(cotxe_id)
    
    # Check if car is already sold
    if cotxe.venut:
        flash("Este coche ya ha sido vendido")
        return redirect(url_for('anuncios'))
    
    # Check if user is trying to make an offer on their own car
    if cotxe.venedor_id == session['user_id']:
        flash("No puedes hacer ofertas en tus propios anuncios")
        return redirect(url_for('anuncios'))
    
    if request.method == "POST":
        usuario_id = session['user_id']
        oferta = float(request.form["oferta"])
        
        mongo.add_oferta(cotxe_id, usuario_id, oferta)
        flash("Oferta enviada correctamente")
        return redirect(url_for('ver_ofertas', cotxe_id=cotxe_id))
    
    return render_template("hacer_oferta.html", cotxe=cotxe)

@app.route("/ofertas/<int:cotxe_id>")
@login_required
def ver_ofertas(cotxe_id):
    cotxe = Cotxe.query.get_or_404(cotxe_id)
    ofertas = mongo.get_ofertes(cotxe_id)
    
    # Get user information for each offer
    for oferta in ofertas:
        usuario = Usuario.query.get(oferta['usuari_id'])
        oferta['nombre_usuario'] = usuario.nom if usuario else "Usuario desconocido"
    
    # Check if current user is the seller
    is_seller = cotxe.venedor_id == session['user_id']
    
    return render_template("ofertas.html", cotxe=cotxe, ofertas=ofertas, is_seller=is_seller)

@app.route("/aceptar-oferta/<int:cotxe_id>/<int:usuari_id>", methods=["POST"])
@login_required
def aceptar_oferta(cotxe_id, usuari_id):
    cotxe = Cotxe.query.get_or_404(cotxe_id)
    
    # Validate that the current user is the seller
    if cotxe.venedor_id != session['user_id']:
        flash("No tienes permiso para aceptar ofertas en este anuncio")
        return redirect(url_for('anuncios'))
    
    ofertas = mongo.get_ofertes(cotxe_id)
    oferta = next((o for o in ofertas if o['usuari_id'] == usuari_id), None)
    
    if oferta:
        # Update offer status
        mongo.update_oferta_status(cotxe_id, usuari_id, 'Acceptada')
        
        # Mark car as sold
        cotxe.venut = True
        
        # Create transaction
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
    
    return redirect(url_for('ver_ofertas', cotxe_id=cotxe_id))

@app.route("/historial-precios/<int:cotxe_id>")
def historial_precios(cotxe_id):
    cotxe = Cotxe.query.get_or_404(cotxe_id)
    historial = mongo.get_preu_history(cotxe_id)
    
    # Format dates
    for item in historial:
        if 'data' in item and item['data']:
            if isinstance(item['data'], str):
                try:
                    date_obj = datetime.fromisoformat(item['data'].replace('Z', '+00:00'))
                    item['data'] = date_obj.strftime("%d/%m/%Y %H:%M")
                except ValueError:
                    pass
            else:
                item['data'] = item['data'].strftime("%d/%m/%Y %H:%M")
    
    return render_template("historial_precios.html", cotxe=cotxe, historial=historial)

@app.route("/comentarios/<int:cotxe_id>", methods=["POST"])
@login_required
def comentarios(cotxe_id):
    if request.method == "POST":
        usuario_id = session['user_id']
        comentario = request.form["comentario"]
        
        # Current timestamp
        current_time = datetime.now()
        # Format for display
        formatted_date = current_time.strftime("%d/%m/%Y %H:%M")
        
        # Store original datetime in MongoDB
        mongo.add_comentari(cotxe_id, usuario_id, comentario)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON response for AJAX requests with formatted date
            usuario = Usuario.query.get(usuario_id)
            return jsonify({
                'nombre_usuario': usuario.nom,
                'comentari': comentario,
                'data': formatted_date
            })
            
        flash("Comentario añadido correctamente")
        return redirect(url_for('detalle_coche', cotxe_id=cotxe_id))

@app.route("/api/charging-stations")
def get_charging_stations():
    lat = request.args.get('latitude')
    lng = request.args.get('longitude')
    api_key = os.getenv('OPENCHARGE_API_KEY')
    
    url = f"https://api.openchargemap.io/v3/poi/"
    params = {
        'output': 'json',
        'countrycode': 'ES',
        'latitude': lat,
        'longitude': lng,
        'distance': 20,
        'distanceunit': 'KM',
        'maxresults': 40,
        'compact': True,
        'verbose': False,
        'key': api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx, 5xx)
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        migrate_json_to_db()
    app.run(debug=True)
