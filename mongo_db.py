from pymongo import MongoClient
from datetime import datetime, timezone

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
    
    # Mètodes de la col·lecció comentaris
    def add_comentari(self, cotxe_id, usuari_id, comentari):
        comentaris_col = self.db.comentaris
        
        # Check si el document per a aquest cotxe existeix
        doc = comentaris_col.find_one({'cotxe_id': cotxe_id})
        
        if doc:
            # Afegir comentari a un document existent
            comentaris_col.update_one(
                {'cotxe_id': cotxe_id},
                {'$push': {'resenyes': {
                    'usuari_id': usuari_id,
                    'comentari': comentari,
                    'data': datetime.now(timezone.utc)
                }}}
            )
        else:
            # Crear un nou document
            comentaris_col.insert_one({
                'cotxe_id': cotxe_id,
                'resenyes': [{
                    'usuari_id': usuari_id,
                    'comentari': comentari,
                    'data': datetime.now(timezone.utc)
                }]
            })
    
    def get_comentaris(self, cotxe_id):
        doc = self.db.comentaris.find_one({'cotxe_id': cotxe_id})
        return doc['resenyes'] if doc else []
    
    # Mètodes de la col·lecció favorits
    def add_favorit(self, usuari_id, cotxe_id):
        favorits_col = self.db.favorits
        
        # Check si un user ja te favorits
        doc = favorits_col.find_one({'usuari_id': usuari_id})
        
        if doc:
            # Afegir a favorits existents si no està present
            if cotxe_id not in doc['cotxes_guardats']:
                favorits_col.update_one(
                    {'usuari_id': usuari_id},
                    {'$push': {'cotxes_guardats': cotxe_id}}
                )
        else:
            # Crear un nou document
            favorits_col.insert_one({
                'usuari_id': usuari_id,
                'cotxes_guardats': [cotxe_id]
            })
    
    def get_favorits(self, usuari_id):
        doc = self.db.favorits.find_one({'usuari_id': usuari_id})
        return doc['cotxes_guardats'] if doc else []
    
    # Mètodes de l'històric de preus
    def add_preu_history(self, cotxe_id, preu):
        historial_col = self.db.historial_preus
        
        historial_col.update_one(
            {'cotxe_id': cotxe_id},
            {'$push': {'preus': {
                'data': datetime.now(timezone.utc),
                'preu': preu
            }}},
            upsert=True
        )
    
    def add_initial_price(self, cotxe_id, precio):
        """Add initial price to history when car is published."""
        now = datetime.now(timezone.utc)
        
        self.db.historial_preus.update_one(
            {'cotxe_id': cotxe_id},
            {'$push': {'preus': {
                'data': now,
                'preu': precio,
                'tipo': 'Precio inicial'
            }}},
            upsert=True
        )
    
    def get_preu_history(self, cotxe_id):
        doc = self.db.historial_preus.find_one({'cotxe_id': cotxe_id})
        return doc['preus'] if doc else []
    
    # Mètodes d'ofertes
    def add_oferta(self, cotxe_id, usuari_id, preu_ofert):
        ofertes_col = self.db.ofertes
        
        ofertes_col.update_one(
            {'cotxe_id': cotxe_id},
            {'$push': {'ofertes': {
                'usuari_id': usuari_id,
                'preu_ofert': preu_ofert,
                'estat': 'Pendent',
                'data': datetime.now(timezone.utc)
            }}},
            upsert=True
        )
    
    def get_ofertes(self, cotxe_id):
        doc = self.db.ofertes.find_one({'cotxe_id': cotxe_id})
        return doc['ofertes'] if doc else []
    
    def update_oferta_status(self, cotxe_id, usuari_id, estat):
        self.db.ofertes.update_one(
            {'cotxe_id': cotxe_id, 'ofertes.usuari_id': usuari_id},
            {'$set': {'ofertes.$.estat': estat}}
        )