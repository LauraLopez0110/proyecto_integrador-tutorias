from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# Configura la conexión a la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/users_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  # Inicializa Flask-Bcrypt

# Define el modelo User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum('admin', 'student', 'teacher'), nullable=False)
    identificacion = db.Column(db.String(50), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(200), nullable=False)

# Define el modelo Compromiso
class Compromiso(db.Model):
    __tablename__ = 'compromiso'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)

# Define el modelo BloqueHorario
class BloqueHorario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False) 
    
    
# Crear la base de datos y las tablas
with app.app_context():
    db.create_all()

# Función para crear un usuario administrador
def create_admin_user():
    username = 'admin'
    password = '1234'  # Cambia por la contraseña deseada
    role = 'admin'
    identificacion = '8787'  # Un identificador único
    nombre_completo = 'Administrador'

    # Verificar si el usuario ya existe
    existing_user = User.query.filter((User.username == username) | (User.identificacion == identificacion)).first()

    if existing_user:
        print('No se puede crear el usuario: ya existe un usuario con el mismo username o identificacion.')
    else:
        # Encriptar la contraseña usando Flask-Bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Crear el usuario
        admin_user = User(username=username, password=hashed_password, role=role, identificacion=identificacion, nombre_completo=nombre_completo)

        # Agregar y guardar en la base de datos
        db.session.add(admin_user)
        db.session.commit()
        print('Usuario administrador creado con éxito.')

# Función para insertar compromisos
def insertar_compromisos():
    compromisos = [
        'Entrega de informe sobre el avance de la tutoría',
        'Revisión de los temas tratados en la última sesión',
        'Entrega del proyecto final de la asignatura',
        'Entrega de los ejercicios prácticos asignados',
        'Elaboración de un resumen de los temas tratados',
        'Envío de materiales adicionales a los estudiantes',
        'Revisión de los compromisos de la tutoría pasada',
        'Evaluación del desempeño del estudiante durante la tutoría'
    ]

    # Insertar compromisos en la base de datos
    for compromiso in compromisos:
        nuevo_compromiso = Compromiso(descripcion=compromiso)
        db.session.add(nuevo_compromiso)

    db.session.commit()
    print("Compromisos insertados correctamente.")
    

# Función para insertar bloques de horarios
def insertar_horarios():
    horarios = [
        {'hora_inicio': '08:00:00', 'hora_fin': '09:00:00'},
        {'hora_inicio': '09:00:00', 'hora_fin': '10:00:00'},
        {'hora_inicio': '10:00:00', 'hora_fin': '11:00:00'},
        {'hora_inicio': '11:00:00', 'hora_fin': '12:00:00'},
        {'hora_inicio': '12:00:00', 'hora_fin': '13:00:00'},
        {'hora_inicio': '13:00:00', 'hora_fin': '14:00:00'},
        {'hora_inicio': '14:00:00', 'hora_fin': '15:00:00'},
        {'hora_inicio': '15:00:00', 'hora_fin': '16:00:00'},
        {'hora_inicio': '16:00:00', 'hora_fin': '17:00:00'},
        {'hora_inicio': '17:00:00', 'hora_fin': '18:00:00'},
    ]

    # Insertar horarios en la base de datos
    for horario in horarios:
        bloque = BloqueHorario(hora_inicio=horario['hora_inicio'], hora_fin=horario['hora_fin'])
        db.session.add(bloque)

    db.session.commit()
    print("Horarios insertados correctamente.")
    
# Llama a la función para crear el usuario
with app.app_context():
    create_admin_user()
    insertar_compromisos()   # Insertar compromisos
    insertar_horarios()      # Insertar horarios
