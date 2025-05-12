from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

# Clase coche principal
class Cotxe():
    def __init__(self, marca, modelo, precio, any, tipo="gasolina/diesel", en_oferta = False):
        # Constructor de la clase Cotxe
        self.tipo = tipo  
        self.marca = marca
        self.modelo = modelo 
        self.precio = round(precio, 2) # Redondeamos a 2 decimales
        self.any = any 
        self.en_oferta = en_oferta

    def mostrar_informacion(self): 
        # Devuelve un mensaje sobre la contaminación
        return f"⛽ Hay que contaminar menos!!!"

    def guardar_en_json(self):
        # Guarda el anuncio en un archivo JSON
        anuncios = self.cargar_anuncios()

        # Mensaje de oferta si el coche tiene descuento
        comentario_oferta = "🚀 Superoferta 21% de descuento!" if self.en_oferta else ""

        anuncios.append({
            "tipo": self.tipo,
            "marca": self.marca,
            "modelo": self.modelo,
            "precio": self.precio,
            "any": self.any,
            "comentario": self.mostrar_informacion(),
            "oferta": comentario_oferta  # Agregamos el comentario de oferta
        })

        # Guardamos la lista de anuncios actualizada en el archivo JSON
        with open("data.json", "w", encoding="utf-8") as file:
            json.dump(anuncios, file, indent=4, ensure_ascii=False)
        
    def cargar_anuncios(self):
        # Carga los anuncios desde el archivo JSON
        try:
            with open("data.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    def crear_desde_diccionario(self, data):
        # Crea un objeto Coche desde un diccionario de datos
        tipo = data.get("tipo", "normal")
        if tipo == "electrico":
            return Cotxeelectric(data["marca"], data["modelo"], float(data["precio"]), data["any"])
        elif tipo == "hibrido":
            return Cotxehybrid(data["marca"], data["modelo"], float(data["precio"]), data["any"])
        else:
           return Cotxe(data["marca"], data["modelo"], float(data["precio"]), data["any"])

    def crear_desde_formulario(self, form):
        # Crea un objeto Coche desde los datos del formulario
        tipo = form["tipo"]
        precio = float(form["precio"])  # Convertimos el precio a número
        any = int(form["any"])  # Convertimos el año a número

        # Verificamos si el coche está en oferta
        en_oferta = "oferta" in form

        if en_oferta:
            precio *= 0.79  # Aplicamos descuento del 21%

        if tipo == "electrico":
            return Cotxeelectric(form["marca"], form["modelo"], precio, any, en_oferta)
        elif tipo == "hibrido":
            return Cotxehybrid(form["marca"], form["modelo"], precio, any, en_oferta)
        else:
            return Cotxe(form["marca"], form["modelo"], precio, any, en_oferta)

    def publicar_anuncio(self):
        # Publica un anuncio de coche
        if request.method == "POST":
            coche = self.crear_desde_formulario(request.form)
            coche.guardar_en_json()
            return redirect(url_for("anuncios"))
        return render_template("publicar.html")

    def ver_anuncios(self):
        # Muestra todos los anuncios de coches
        anuncios = self.cargar_anuncios()
        return render_template("anuncios.html", anuncios=anuncios)

    def buscar(self, precio=None, anyo=None, tipo=None):
        # Busca coches filtrando por precio, año y tipo
        anuncios = self.cargar_anuncios()
        if precio is not None:
            anuncios = [anuncio for anuncio in anuncios if anuncio["precio"] <= precio]
        if anyo is not None:
            anuncios = [anuncio for anuncio in anuncios if anuncio["any"] == anyo]
        if tipo is not None:
            anuncios = [anuncio for anuncio in anuncios if anuncio["tipo"] == tipo]
        return anuncios

# Subclases de Cotxe (herencias)
class Cotxehybrid(Cotxe):
    def __init__(self, marca, modelo, precio, any, en_oferta = False):
        # Crea un coche híbrido
        super().__init__(marca, modelo, precio, any, tipo="hibrido", en_oferta = en_oferta)

    def mostrar_informacion(self): #Polimorfismos
        return f"⚡⛽ ¡Ahorra combustible!"

class Cotxeelectric(Cotxe):
    def __init__(self, marca, modelo, precio, any, en_oferta = False):
        # Crea un coche eléctrico
        super().__init__(marca, modelo, precio, any, tipo="electrico", en_oferta = en_oferta)

    def mostrar_informacion(self): #Polimorfismos
        return f"⚡ Cero emisiones!"

# Clase Usuario (de momento no sirve)
class Usuario(): 
    def __init__(self, nombre, dni, localidad):
        # Constructor de la clase Usuario
        self.nombre = nombre
        self.dni = dni
        self.localidad = localidad

# Rutas de la aplicación Flask
@app.route("/")
def index():
    return render_template("index.html")  # Muestra la pagina principal

@app.route("/anuncios")
def anuncios():
    # Carga y muestra todos los anuncios de coches
    cotxe = Cotxe("marca", "modelo", 10000, 2021)  
    return cotxe.ver_anuncios()

@app.route("/publicar", methods=["GET", "POST"]) 
def publicar():
    # Ruta para publicar un nuevo anuncio de coche
    cotxe = Cotxe("marca", "modelo", 10000, 2021)  
    return cotxe.publicar_anuncio()

@app.route("/buscar", methods=["GET"])
def buscar():
    # Filtra los anuncios según los parámetros de búsqueda
    marca = request.args.get("marca", "").lower()
    modelo = request.args.get("modelo", "").lower()
    precio_max = request.args.get("precio")
    anyo = request.args.get("any")

    cotxe = Cotxe("marca", "modelo", 10000, 2021)
    anuncios = cotxe.cargar_anuncios()

# Aplicar filtros sobre la lista de anuncios cargados

    resultados = [
        anuncio for anuncio in anuncios
        if (not marca or marca in anuncio["marca"].lower())
        and (not modelo or modelo in anuncio["modelo"].lower())
        and (not precio_max or float(anuncio["precio"]) <= float(precio_max))
        and (not anyo or int(anuncio["any"]) == int(anyo))
    ]

    return render_template("buscar.html", anuncios=resultados)

if __name__ == "__main__":
    app.run(debug=True)
