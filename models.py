from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum('student', 'teacher', 'admin'), nullable=False)
    identificacion = db.Column(db.String(50), unique=True, nullable=False)  
    nombre_completo = db.Column(db.String(200), nullable=False)

class Tutoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    espacio_academico = db.Column(db.String(100), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    docente = db.relationship('User', backref='tutorias')  # Relación inversa

class Estudiante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    semestre = db.Column(db.String(20))
    programa_academico = db.Column(db.String(100))
    estado = db.Column(db.Enum('Activo', 'Inactivo', 'Graduado'))
    estudiante_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))

    estudiante = db.relationship('User', backref='estudiantes')  # Relación inversa
    
class Docente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    departamento = db.Column(db.String(100))
    correo_institucional = db.Column(db.String(100), unique=True, nullable=False)
    fecha_ingreso = db.Column(db.Date, nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))

    docente = db.relationship('User', backref='docentes')  # Relación inversa
    
class BloqueHorario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)

    def __repr__(self):

        return f"{self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')}"

class HorariosTutoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutoria_id = db.Column(db.Integer, db.ForeignKey('tutoria.id'))
    bloque_horario_id = db.Column(db.Integer, db.ForeignKey('bloque_horario.id'))
    estado = db.Column(db.Enum('Disponible', 'No disponible'), nullable=False)
    
    bloque_horario = db.relationship('BloqueHorario', backref='horarios_tutoria')
    tutoria = db.relationship('Tutoria', backref='horarios')
    
class Inscripcion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    tutoria_id = db.Column(db.Integer, db.ForeignKey('tutoria.id', ondelete='CASCADE'))
    horario_id = db.Column(db.Integer, db.ForeignKey('horarios_tutoria.id', ondelete='CASCADE'))
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)

    estudiante = db.relationship('User', backref='inscripciones')
    tutoria = db.relationship('Tutoria', backref='inscripciones')
    horario = db.relationship('HorariosTutoria', backref='inscripciones')


class FormatoTutoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    periodo_academico = db.Column(db.String(50), nullable=False)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    codigo_estudiante = db.Column(db.String(20), nullable=False)
    semestre_estudiante = db.Column(db.String(20), nullable=False)
    asignatura = db.Column(db.String(100), nullable=False)  # Equivalente a espacio académico
    temas_tratados = db.Column(db.Text, nullable=True)
    fecha = db.Column(db.Date, nullable=False)

    docente = db.relationship('User', foreign_keys=[docente_id], backref='formatos_docente')
    estudiante = db.relationship('User', foreign_keys=[estudiante_id], backref='formatos_estudiante')


class Compromiso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    
class FormatoTutoriaCompromiso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    formato_tutoria_id = db.Column(db.Integer, db.ForeignKey('formato_tutoria.id', ondelete='CASCADE'))
    compromiso_id = db.Column(db.Integer, db.ForeignKey('compromiso.id', ondelete='CASCADE'))
    
    tutoria = db.relationship('FormatoTutoria', backref='compromisos')
    compromiso = db.relationship('Compromiso', backref='formatos_tutorias')