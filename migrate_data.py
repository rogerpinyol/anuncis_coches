# probablement no ho utilizare pero es una bona eina per si em fa falta
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
                tipo = anuncio["tipo"]
                if tipo == "electrico":
                    car_type = "Electric"
                    car_class = CotxeElectric
                elif tipo == "hibrido":
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