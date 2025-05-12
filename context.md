# Car Marketplace Simulator Context

## Project Overview
This project is a Flask-based Python application designed to manage a second-hand car marketplace. It allows users to post, browse, and purchase cars, with data stored in both relational (MariaDB) and non-relational (MongoDB) databases. The application supports user management, car listings, transactions, comments, price history, favorites, and offers.

## Database Structure

### MariaDB (Relational Database)
Stores structured and relational data for users, cars, and transactions.

#### Table: `usuaris` (Users)
Stores user information for buyers and sellers.
```sql
CREATE TABLE usuaris (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    pass VARCHAR(50),
    tipus ENUM('Comprador', 'Venedor')
);
```

#### Table: `cotxes` (Cars)
Stores information about cars for sale.
```sql
CREATE TABLE cotxes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    venedor_id INT,
    marca VARCHAR(50),
    model VARCHAR(50),
    any INT,
    preu DECIMAL(10,2),
    tipus ENUM('Gasolina', 'Diesel', 'Electric', 'Híbrid'),
    autonomia INT, -- Only for electric and hybrid cars
    FOREIGN KEY (venedor_id) REFERENCES usuaris(id)
);
```

#### Table: `transaccions` (Transactions)
Records completed car purchases.
```sql
CREATE TABLE transaccions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    comprador_id INT,
    cotxe_id INT,
    preu_final DECIMAL(10,2),
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (comprador_id) REFERENCES usuaris(id),
    FOREIGN KEY (cotxe_id) REFERENCES cotxes(id)
);
```

### MongoDB (Non-Relational Database)
Stores dynamic and flexible data for comments, favorites, price history, and offers.

#### Collection: `comentaris` (Comments)
Stores user reviews for cars or sellers.
```json
{
    "cotxe_id": 2,
    "resenyes": [
        {"usuari_id": 5, "comentari": "Good condition, price a bit high", "data": "2024-02-01"},
        {"usuari_id": 7, "comentari": "Works perfectly!", "data": "2024-02-03"}
    ]
}
```

#### Collection: `favorits` (Favorites)
Stores cars saved by buyers for later review.
```json
{
    "usuari_id": 3,
    "cotxes_guardats": [5, 12, 18]
}
```

#### Collection: `historial_preus` (Price History)
Tracks price changes for a car over time.
```json
{
    "cotxe_id": 10,
    "preus": [
        {"data": "2024-01-10", "preu": 15000},
        {"data": "2024-02-01", "preu": 14500}
    ]
}
```

#### Collection: `ofertes` (Offers)
Manages offers made by buyers for cars.
```json
{
    "cotxe_id": 8,
    "ofertes": [
        {"usuari_id": 4, "preu_ofert": 18000, "estat": "Pendent"},
        {"usuari_id": 6, "preu_ofert": 18500, "estat": "Acceptada"}
    ]
}
```

## Interaction Between MariaDB and MongoDB
The application integrates MariaDB and MongoDB to handle different aspects of the marketplace workflow:
1. **Seller posts a car**: Stored in MariaDB (`cotxes` table).
2. **Buyer saves a car as favorite**: Stored in MongoDB (`favorits` collection).
3. **Buyer makes an offer for a car**: Stored in MongoDB (`ofertes` collection).
4. **Seller accepts an offer, and the car is sold**: Offer moves from MongoDB (`ofertes`) to MariaDB (`transaccions` table).
5. **Buyer writes a review for the car**: Stored in MongoDB (`comentaris` collection).
6. **View car price history**: Retrieved from MongoDB (`historial_preus` collection).

## ORM Usage
To simplify database interactions, the project will use an Object-Relational Mapping (ORM) tool for MariaDB. Since the developer is new to ORMs, SQLAlchemy is recommended for its flexibility and compatibility with Flask. For MongoDB, PyMongo will be used directly, as it is well-suited for NoSQL operations and aligns with MongoDB's dynamic schema.

### Recommended Tools
- **SQLAlchemy**: For managing MariaDB tables (`usuaris`, `cotxes`, `transaccions`) with Python classes and relationships.
- **PyMongo**: For interacting with MongoDB collections (`comentaris`, `favorits`, `historial_preus`, `ofertes`).

## Additional Notes
- The application is built using Flask to handle HTTP requests and render templates for the user interface.
- Data is persisted in JSON files as a fallback or for specific use cases (e.g., initial data seeding).
- Ensure proper foreign key constraints in MariaDB to maintain referential integrity.
- MongoDB collections should be indexed on `cotxe_id` and `usuari_id` for efficient queries.
- The ORM setup should include clear mappings for MariaDB tables and handle relationships (e.g., `venedor_id` and `comprador_id` foreign keys).

This context provides a comprehensive foundation for developing or extending the car marketplace simulator.