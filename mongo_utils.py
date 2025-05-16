from datetime import datetime, timezone

def add_comentari(self, cotxe_id, usuari_id, comentari):
    """Add a comment to a car."""
    now = datetime.now()
    comentari_doc = {
        'cotxe_id': cotxe_id,
        'usuari_id': usuari_id,
        'comentari': comentari,
        'data': now
    }
    self.db.comentaris.insert_one(comentari_doc)
    return comentari_doc

def add_oferta(self, cotxe_id, usuari_id, preu_ofert):
    """Add an offer for a car."""
    now = datetime.now()
    oferta_doc = {
        'cotxe_id': cotxe_id,
        'usuari_id': usuari_id,
        'preu_ofert': preu_ofert,
        'estat': 'Pendent',
        'data': now
    }
    self.db.ofertes.insert_one(oferta_doc)
    return oferta_doc

def accept_oferta(self, cotxe_id, usuari_id, precio_actual):
    """Accept an offer and update price history."""
    now = datetime.now(timezone.utc)
    
    # Update offer status
    self.db.ofertes.update_one(
        {'cotxe_id': cotxe_id, 'usuari_id': usuari_id, 'estat': 'Pendent'},
        {'$set': {'estat': 'Aceptada'}}
    )
    
    # Get the accepted offer
    oferta = self.db.ofertes.find_one(
        {'cotxe_id': cotxe_id, 'usuari_id': usuari_id, 'estat': 'Aceptada'}
    )
    
    # Add to price history only when an offer is accepted
    if oferta:
        self.add_price_change(cotxe_id, oferta['preu_ofert'], tipo='Oferta aceptada')
    
    return oferta

def add_initial_price(self, cotxe_id, precio):
    """Add initial price to history when car is published."""
    now = datetime.now(timezone.utc)
    
    history_entry = {
        'preu': precio,
        'data': now,
        'tipo': 'Precio inicial'
    }
    
    self.db.historial_preus.update_one(
        {'cotxe_id': cotxe_id},
        {'$push': {'preus': history_entry}},
        upsert=True
    )

def add_price_change(self, cotxe_id, nuevo_precio, tipo='Cambio de precio'):
    """Add price change to history."""
    now = datetime.now(timezone.utc)
    
    history_entry = {
        'preu': nuevo_precio,
        'data': now,
        'tipo': tipo
    }
    
    self.db.historial_preus.update_one(
        {'cotxe_id': cotxe_id},
        {'$push': {'preus': history_entry}},
        upsert=True
    )