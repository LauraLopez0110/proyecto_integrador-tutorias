from flask import Flask, render_template, redirect, url_for, flash, session, request, send_file
from flask_bcrypt import Bcrypt
from flask_login import current_user, login_required
from config import Config
from models import db, User,Tutoria, Estudiante, Docente, HorariosTutoria
from models import Inscripcion,FormatoTutoria, Compromiso, FormatoTutoriaCompromiso
# Importa db y User, Tutoria
from datetime import datetime, timezone
import io
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
app.config.from_object(Config)  # Carga la configuración desde el objeto Config
db.init_app(app)  # Inicializa la base de datos con la app
bcrypt = Bcrypt(app)  # Inicializa Flask-Bcrypt para manejar el hash de contraseñas

# Función para liberar las tutorías programadas

def liberar_tutorias():
    inscripciones = Inscripcion.query.all()
    for inscripcion in inscripciones:
        horario = HorariosTutoria.query.get(inscripcion.horario_id)
        
        try:
            # Separar la hora en dos partes (inicio y fin)
            horas = horario.hora.split(' - ')
            hora_inicio = datetime.strptime(horas[0].strip(), '%I:%M %p')  # Convertir hora de inicio
            hora_fin = datetime.strptime(horas[1].strip(), '%I:%M %p')  # Convertir hora de fin

            # Si la tutoría ya pasó, liberar el horario
            if hora_inicio < datetime.now():
                horario.estado = 'Disponible'  # Liberar el horario
                db.session.delete(inscripcion)  # Eliminar inscripción

        except ValueError as e:
            print(f"Error al convertir la hora: {horario.hora} - {e}")
    
    db.session.commit()
    print(f"Tutorías liberadas automáticamente el {datetime.utcnow()}.")

# Iniciar el cron job
scheduler = BackgroundScheduler()
scheduler.add_job(liberar_tutorias, 'cron', day_of_week='fri', hour=23, minute=59)  # Cada viernes a las 11:59 PM
scheduler.start()

@app.route('/liberar')
def liberar():
    liberar_tutorias()  # Llamada manual
    return "Tutorías liberadas correctamente."
    
# Define la función para verificar si el código de tutoría existe
def codigo_tutoria_existe(codigo, tutoria_id=None):
    query = Tutoria.query.filter_by(codigo=codigo)
    if tutoria_id:
        query = query.filter(Tutoria.id != tutoria_id)  # Excluye la tutoría que se está editando
    return query.first() is not None

def generar_codigo_tutoria(espacio_academico):
    
    
    # Extraer las iniciales de cada palabra en el nombre de la materia
    iniciales = ''.join([palabra[0] for palabra in espacio_academico.upper().split()])
    
    # Obtener el año actual
    anio = datetime.now().year
    
    # Determinar el semestre (ejemplo: de enero a junio es 1, de julio a diciembre es 2)
    mes = datetime.now().month
    semestre = 1 if mes <= 6 else 2
    
    
    # Concatenar todos los componentes para formar el código
    codigo_tutoria = f"{iniciales}{anio}-{semestre}"
    
    return codigo_tutoria

def crear_estudiante(form, new_user):
    codigo = form.get('codigo')
    semestre = form.get('semestre')
    programa_academico = form.get('programa_academico')
    estado = form.get('estado', 'Activo')  # Estado predeterminado: 'Activo'

    # Crear el estudiante y asociarlo al usuario recién creado
    estudiante = Estudiante(codigo=codigo, semestre=semestre, programa_academico=programa_academico, 
                            estado=estado, estudiante_id=new_user.id)

    db.session.add(estudiante)  # Agregar el estudiante a la sesión
    db.session.commit()  # Guardar el estudiante en la base de datos


def crear_docente(form, new_user):
    departamento = form.get('departamento')
    correo_institucional = form.get('correo_institucional')
    fecha_ingreso = form.get('fecha_ingreso')

    # Crear el docente y asociarlo al usuario recién creado
    docente = Docente(departamento=departamento, correo_institucional=correo_institucional, 
                      fecha_ingreso=fecha_ingreso, docente_id=new_user.id)

    db.session.add(docente)  # Agregar el docente a la sesión
    db.session.commit()  # Guardar el docente en la base de datos



@app.route('/')
def home():
    # Si el usuario ya ha iniciado sesión, redirigir al dashboard según el rol
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('dashboard'))
        elif role == 'teacher':
            return redirect(url_for('dashboard'))
        elif role == 'student':
            return redirect(url_for('dashboard'))
    # Si no ha iniciado sesión, redirigir a la página de login
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya ha iniciado sesión, redirige al dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    # Manejo de la lógica de inicio de sesión
    if request.method == 'POST':
        username = request.form['username'].strip()  # Eliminamos espacios innecesarios
        password = request.form['password']
        user = User.query.filter(User.username.ilike(username)).first()  # Utiliza ilike para la búsqueda

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # endpoint Muestra el panel de control del usuario
    if 'username' in session:
        user = db.session.get(User, session['user_id'])
        
         # Si es un docente, puedes obtener sus tutorías o hacer otras acciones
        # Si el usuario es un docente, obtenemos sus tutorías
        if user.role == 'teacher':
            tutorias = Tutoria.query.filter_by(docente_id=user.id).all()  # Obtener tutorías asociadas al docente
            return render_template('dashboard.html', username=session['username'], role=session['role'], user=user, tutorias=tutorias, docente=user)  # Pasar el docente
        
  # Obtiene el usuario de la base de datos
        return render_template('dashboard.html', username=session['username'], role=session['role'], user=user)  # Pasa el usuario a la plantilla
    flash('Debes iniciar sesión primero', 'danger')  # Mensaje de error si no hay sesión
    return redirect(url_for('login'))  # Redirige a la página de inicio de sesión

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Manejo del registro de nuevos usuarios
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # Obtiene el rol del formulario
        identificacion = request.form['identificacion']  # Obtiene la identificación
        nombre_completo = request.form['nombre_completo']  # Obtiene el nombre completo
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Hash de la contraseña
        
        # Verifica si el nombre de usuario o la identificación ya existen
        existing_user = User.query.filter(
            (User.username.ilike(username)) | (User.identificacion == identificacion)
        ).first()

        if existing_user:
            # Comprobar si el nombre de usuario ya existe (esto se hace en la consulta)
            if existing_user.username.lower() == username.lower():  # Comparación sin distinción de mayúsculas
                flash('El nombre de usuario ya está en uso. Elige otro.', 'danger')
            # Comprobar si la identificación ya existe
            if existing_user.identificacion == identificacion:
                flash('La identificación ya está registrada. Elige otra.', 'danger')
            return redirect(url_for('register'))  # Redirige si ya existe el usuario

        # Si el nombre de usuario y la identificación son únicos, crea el nuevo usuario
        new_user = User(username=username, password=hashed_password, role=role, identificacion=identificacion,
                        nombre_completo=nombre_completo)
        db.session.add(new_user)  # Agrega el nuevo usuario a la sesión
        db.session.commit()  # Guarda los cambios en la base de datos
        
         # Si el usuario es estudiante, crea el objeto estudiante y lo asocia al usuario
        if role == 'student':
            crear_estudiante(request.form, new_user)

        # Si el usuario es docente, crea el objeto docente y lo asocia al usuario
        if role == 'teacher':
            crear_docente(request.form, new_user)
        flash('Registro exitoso', 'success')  # Mensaje de éxito
        return redirect(url_for('login'))  # Redirige a la página de inicio de sesión

    return render_template('register.html')  # Renderiza la plantilla de registro



@app.route('/logout')
def logout():
    # endpoint Maneja el cierre de sesión
    session.clear()  # Limpia la sesión
    flash('Has cerrado sesión', 'success')  # Mensaje de éxito
    return redirect(url_for('login'))  # Redirige a la página de inicio de sesión

@app.route('/admin/users', methods=['GET', 'POST'])
def manage_users():
    if 'username' not in session or session['role'] != 'admin':
        flash('Acceso denegado. Solo los administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('dashboard'))

    users = User.query.all()  # Obtiene todos los usuarios

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')

        if action == 'delete':
            if int(user_id) == session['user_id']:
                flash('No puedes eliminar tu propio usuario.', 'danger')
            else:
                user_to_delete = User.query.get(user_id)
                # Verificar si el usuario tiene tutorías asociadas
                if user_to_delete and user_to_delete.tutorias:  # verifica relación del usuario existente con tutorías asociadas
                    flash('No se puede eliminar el usuario porque tiene tutorías asociadas.', 'danger')
                elif user_to_delete:
                    # Si el usuario es un estudiante, elimina también el estudiante
                    if user_to_delete.role == 'student':
                        estudiante_to_delete = Estudiante.query.filter_by(estudiante_id=user_to_delete.id).first()
                        if estudiante_to_delete:
                            db.session.delete(estudiante_to_delete)
                            
                    #Si el usuario es un docente, elimina también el docente
                    if user_to_delete.role == 'teacher':
                        docente_to_delete = Docente.query.filter_by(docente_id=user_to_delete.id).first()
                        if docente_to_delete:
                            db.session.delete(docente_to_delete)
                            
                    db.session.delete(user_to_delete)
                    db.session.commit()
                    flash('Usuario eliminado exitosamente.', 'success')
                else:
                    flash('Usuario no encontrado.', 'danger')

            # Añadimos redirección para que la página se recargue tras eliminar o editar un usuario
            return redirect(url_for('manage_users'))

    return render_template('manage_users.html', users=users)

@app.route('/student_profile', methods=['GET'])
def student_profile():
    # Obtener el ID del usuario logueado
    current_user_id = session.get('user_id')
    

    # Verificar si el usuario está en sesión
    if not current_user_id:
        flash("Por favor, inicia sesión", "danger")
        return redirect(url_for('login'))  # Redirige a la página de inicio de sesión si no está logueado

    # Obtener el estudiante por el ID del usuario logueado
    estudiante = Estudiante.query.filter_by(estudiante_id=current_user_id).first()
    
    # Verificar si el estudiante existe
    if not estudiante:
        flash("Estudiante no encontrado", "danger")
        return redirect(url_for('dashboard'))  # Redirige a una página válida

    # Renderiza el template con los datos del estudiante
    return render_template('student_profile.html', estudiante=estudiante)

@app.route('/teacher_profile', methods=['GET'])
def teacher_profile():
    # Obtener el ID del usuario logueado
    current_user_id = session.get('user_id')

    # Verificar si el usuario está en sesión
    if not current_user_id:
        flash("Por favor, inicia sesión", "danger")
        return redirect(url_for('login'))  # Redirige a la página de inicio de sesión si no está logueado

    # Obtener el profesor por el ID del usuario logueado
    profesor = Docente.query.filter_by(docente_id=current_user_id).first()
    
    # Verificar si el profesor existe
    if not profesor:
        flash("Profesor no encontrado", "danger")
        return redirect(url_for('dashboard'))  # Redirige a una página válida

    # Renderiza el template con los datos del profesor
    return render_template('teacher_profile.html', profesor=profesor)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    
    user = db.session.get(User, user_id)
    est = Estudiante.query.filter_by(estudiante_id=user_id).first() if user.role == 'student' else None
    doc = Docente.query.filter_by(docente_id=user_id).first() if user.role == 'teacher' else None
    
    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('manage_users'))

    current_user_id = session['user_id']

    if request.method == 'POST':
        username = request.form['username']
        identificacion = request.form['identificacion']
        role = request.form['role']
        nombre_completo = request.form['nombre_completo']

        new_password = request.form['password']  # Nueva contraseña desde el formulario

        if user_id == current_user_id:
            if role != user.role:
                flash('No puedes cambiar tu propio rol.', 'warning')
                return redirect(url_for('edit_user', user_id=user_id))

        existing_user = User.query.filter(
            ((User.username == username) | (User.identificacion == identificacion)) &
            (User.id != user_id)
        ).first()

        if existing_user:
            if existing_user.username == username:
                flash('El nombre de usuario ya está en uso. Elige otro.', 'danger')
            if existing_user.identificacion == identificacion:
                flash('La identificación ya está registrada. Elige otra.', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))

        user.username = username
        user.identificacion = identificacion
        user.nombre_completo = nombre_completo    
        if user_id != current_user_id:
            user.role = role
        
        
        # Actualiza la contraseña solo si se proporciona una nueva
        if new_password:
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user.password = hashed_password   
        # Si el rol es 'student', actualizamos o creamos los datos del estudiante
        if role == 'student':
            if est:
                est.codigo = request.form['codigo']
                est.semestre = request.form['semestre']
                est.programa_academico = request.form['programa_academico']
                est.estado = request.form['estado']
            else:
                # Si no existe, crea una nueva entrada para estudiante
                new_student = Estudiante(
                    estudiante_id=user_id,
                    codigo=request.form['codigo'],
                    semestre=request.form['semestre'],
                    programa_academico=request.form['programa_academico'],
                    estado=request.form['estado']
                )
                db.session.add(new_student) 

        # Si el rol es 'teacher', actualizamos o creamos los datos del docente
        elif role == 'teacher':
            if doc:
                doc.departamento = request.form['departamento']
                doc.correo_institucional = request.form['correo_institucional']
                doc.fecha_ingreso = request.form['fecha_ingreso']
            else:
                # Si no existe, crea una nueva entrada para docente
                new_teacher = Docente(
                    docente_id=user_id,
                    departamento=request.form['departamento'],
                    correo_institucional=request.form['correo_institucional'],
                    fecha_ingreso=request.form['fecha_ingreso']
                )
                db.session.add(new_teacher)  # Aquí se debe agregar la sesión para el docente

        db.session.commit()
        flash('Usuario actualizado exitosamente.', 'success')
        return redirect(url_for('manage_users'))

    return render_template('edit_user.html', user=user, est=est, doc=doc)

@app.route('/admin/users/detalle_user/<int:user_id>', methods=['GET'])
def detalle_user(user_id):
    # Obtener el usuario general
    user = User.query.get(user_id)
    
    # Verificar si el usuario existe
    if not user:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for('admin_users'))

    # Obtener detalles específicos si el usuario es estudiante o docente
    estudiante = Estudiante.query.filter_by(estudiante_id=user.id).first() if user.role == 'student' else None
    docente = Docente.query.filter_by(docente_id=user.id).first() if user.role == 'teacher' else None

    # Renderizar la plantilla con los detalles del usuario
    return render_template('detalle_user.html', user=user, estudiante=estudiante, docente=docente)

    
@app.route('/admin/tutorias', methods=['GET', 'POST'])
def manage_tutorias():
    if 'username' not in session or session['role'] != 'admin':
        flash('Acceso denegado. Solo los administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        codigo = generar_codigo_tutoria(request.form['espacio_academico'])
        espacio_academico = request.form['espacio_academico']
        docente_id = request.form['docente']

        if codigo_tutoria_existe(codigo):
            flash('El código de la tutoría ya existe. Por favor, usa uno diferente.', 'danger')
            return redirect(url_for('manage_tutorias'))

        new_tutoria = Tutoria(codigo=codigo, espacio_academico=espacio_academico, docente_id=docente_id)
        db.session.add(new_tutoria)
        db.session.commit()
        flash('Tutoría creada exitosamente.', 'success')
        return redirect(url_for('manage_tutorias'))

    docentes = User.query.filter_by(role='teacher').all()
    tutorias = Tutoria.query.all()
    return render_template('manage_tutorias.html', tutorias=tutorias, docentes=docentes)


@app.route('/admin/tutorias/delete/<int:tutoria_id>', methods=['POST'])
def delete_tutoria(tutoria_id):
    if 'username' not in session or session['role'] != 'admin':
        flash('Acceso denegado. Solo los administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('dashboard'))

    tutoria_to_delete = Tutoria.query.get(tutoria_id)
    if tutoria_to_delete:
        db.session.delete(tutoria_to_delete)
        db.session.commit()
        flash('Tutoría eliminada exitosamente.', 'success')
    else:
        flash('Tutoría no encontrada.', 'danger')
    
    return redirect(url_for('manage_tutorias'))

@app.route('/admin/tutorias/edit/<int:tutoria_id>', methods=['GET', 'POST'])
def edit_tutoria(tutoria_id):
    if 'username' not in session or session['role'] != 'admin':
        flash('Acceso denegado. Solo los administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('dashboard'))

    tutoria_to_edit = Tutoria.query.get(tutoria_id)
    if not tutoria_to_edit:
        flash('Tutoría no encontrada.', 'danger')
        return redirect(url_for('manage_tutorias'))

    if request.method == 'POST':
        codigo = request.form['codigo']
        espacio_academico = request.form['espacio_academico']
        docente_id = request.form['docente']


        palabras = espacio_academico.split()
        iniciales = ''.join([palabra[0].upper() for palabra in palabras])
        codigo = f"{iniciales}2024-2"

        if codigo_tutoria_existe(codigo, tutoria_id):
            flash('El código de la tutoría ya existe. Por favor, usa uno diferente.', 'danger')
            return redirect(url_for('edit_tutoria', tutoria_id=tutoria_id))

        tutoria_to_edit.codigo = codigo
        tutoria_to_edit.espacio_academico = espacio_academico
        tutoria_to_edit.docente_id = docente_id

        db.session.commit()
        flash('Tutoría editada exitosamente.', 'success')
        return redirect(url_for('manage_tutorias'))

    docentes = User.query.filter_by(role='teacher').all()
    return render_template('edit_tutoria.html', tutoria=tutoria_to_edit, docentes=docentes)


@app.route('/profile/edit', methods=['GET', 'POST']) 
def edit_profile():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero', 'danger')
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    est = Estudiante.query.filter_by(estudiante_id=user.id).first() if user.role == 'student' else None
    doc = Docente.query.filter_by(docente_id=user.id).first() if user.role == 'teacher' else None
    
    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        identificacion = request.form['identificacion'].strip()
        nombre_completo = request.form['nombre_completo'].strip()
        new_password = request.form['password']

        # Verifica si el nuevo username o identificacion ya existen en otros usuarios
        existing_user = User.query.filter(
            ((User.username.ilike(username)) | (User.identificacion == identificacion)) &
            (User.id != user.id)
        ).first()

        if existing_user:
            if existing_user.username.lower() == username.lower():
                flash('El nombre de usuario ya está en uso. Elige otro.', 'danger')
            if existing_user.identificacion == identificacion:
                flash('La identificación ya está registrada. Elige otra.', 'danger')
            return redirect(url_for('edit_profile'))

        # Actualiza los campos básicos
        user.username = username
        user.identificacion = identificacion
        user.nombre_completo = nombre_completo

        # Actualiza la contraseña solo si se proporciona una nueva
        if new_password:
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user.password = hashed_password


        # Actualiza los datos según el rol
        if user.role == 'student':
            if est:
                est.codigo = request.form['codigo']
                est.semestre = request.form['semestre']
                est.programa_academico = request.form['programa_academico']
                est.estado = request.form['estado']

        elif user.role == 'teacher':
            if doc:
                doc.departamento = request.form['departamento']
                doc.correo_institucional = request.form['correo_institucional']
                doc.fecha_ingreso = request.form['fecha_ingreso']

        db.session.commit()
        flash('Perfil actualizado exitosamente.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_profile.html', user=user, doc=doc, est=est)



@app.route('/teacher/<int:docente_id>/tutorias', methods=['GET', 'POST'])
def listar_tutorias_por_docente(docente_id):
    user = db.session.get(User, session['user_id'])  # Obtiene el usuario de la sesión
    docente = User.query.filter_by(id=docente_id, role='teacher').first()
    
    if not docente:
        flash("Docente no encontrado", "danger")
        return redirect(url_for('dashboard'))

    # Manejo de acciones POST
    if request.method == 'POST':
        if 'eliminar_horario' in request.form:
            horario_id = request.form.get('horario_id')
            horario = HorariosTutoria.query.get(horario_id)

            if horario:
                db.session.delete(horario)
                db.session.commit()
                flash("Horario eliminado con éxito.", "success")
            else:
                flash("Horario no encontrado.", "danger")


        return redirect(url_for('listar_tutorias_por_docente', docente_id=docente_id))

    # Obtener las tutorías del docente
    tutorias = Tutoria.query.filter_by(docente_id=docente_id).all()

    return render_template('teacher_tutorias.html', docente=docente, tutorias=tutorias, user=user)


@app.route('/teacher/asignar_horarios/<int:tutoria_id>', methods=['GET', 'POST'])
def asignar_horarios_tutorias(tutoria_id):
    user = db.session.get(User, session['user_id'])  # Obtiene el usuario de la sesión
    
    if not user or user.role != 'teacher':
        flash("Acceso denegado. Solo los docentes pueden acceder a esta sección.", "danger")
        return redirect(url_for('dashboard'))
    
    # Obtener la tutoría específica usando tutoria_id
    tutoria = Tutoria.query.filter_by(id=tutoria_id).first()  # Obtiene solo un registro
    
    if not tutoria:
        flash('Tutoría no encontrada', 'error')
        return redirect(url_for('dashboard'))  # Redirige al dashboard si la tutoría no existe

    if request.method == 'POST':
        dia = request.form.get('dia')  # Día seleccionado
        hora = request.form.get('hora')  # Hora seleccionada

        # Validar que se haya seleccionado un día y una hora
        if not dia or not hora:
            flash('Debe seleccionar tanto el día como la hora', 'danger')
            return render_template('asignar_horario.html', tutoria=tutoria)
        
        # Validar que no haya otro horario asignado para esa tutoría y docente
        existing_horario = HorariosTutoria.query.filter_by(tutoria_id=tutoria_id, dia=dia, hora=hora).first()
        
        if existing_horario:
            flash('Ya existe un horario asignado para esta tutoría en esa hora y día', 'danger')
            return render_template('asignar_horario.html', tutoria=tutoria)

        # Crear el nuevo horario
        new_horario = HorariosTutoria(
            tutoria_id=tutoria_id,
            dia=dia,
            hora=hora,
            estado='Disponible'
        )
        db.session.add(new_horario)
        db.session.commit()

        flash('Horario asignado correctamente', 'success')
        return redirect(url_for('listar_tutorias_por_docente', docente_id=user.id))  # Redirige al dashboard del docente

    # Si la solicitud es GET, se muestra el formulario para asignar horario
    return render_template('asignar_horario.html', tutoria=tutoria)


@app.route('/student/inscribirse/<int:tutoria_id>', methods=['GET', 'POST'])
def inscribirse_tutoria(tutoria_id):
    
    user = db.session.get(User, session['user_id'])
    
    if not user or user.role != 'student':
        flash("Acceso denegado. Solo los estudiantes pueden acceder a esta sección.", "danger")
        return redirect(url_for('dashboard'))

    tutoria = Tutoria.query.get(tutoria_id)
    if not tutoria:
        flash("Tutoría no encontrada.", "danger")
        return redirect(url_for('dashboard'))

    # Obtener el docente relacionado con esta tutoría
    docente = tutoria.docente  # Asegúrate que la tutoría tiene una relación con el docente (User)
    if docente:
        docente_detalles = Docente.query.filter_by(docente_id=docente.id).first()
    
    # Obtener el horario ya asignado para esta tutoría
    horario_asignado = HorariosTutoria.query.filter(
        HorariosTutoria.tutoria_id == tutoria_id,
        HorariosTutoria.estado == 'Disponible',  # Solo horarios disponibles
        ~HorariosTutoria.inscripciones.any()  # Horarios sin inscripciones
    ).first()

    if not horario_asignado:
        flash("No hay horarios disponibles para esta tutoría.", "danger")
        return redirect(url_for('dashboard'))
    
    # Mostrar mensaje sobre días festivos
    flash("Recuerda que no hay tutorías los días festivos.", "info")


    if request.method == 'POST':
        # Verificar si el estudiante ya está inscrito en esta tutoría
        inscripcion_existente = Inscripcion.query.filter_by(estudiante_id=user.id, tutoria_id=tutoria_id).first()
        if inscripcion_existente:
            flash("Ya estás inscrito en esta tutoría.", "warning")
            return redirect(url_for('dashboard'))

        # Crear inscripción en el horario asignado
        nueva_inscripcion = Inscripcion(estudiante_id=user.id, tutoria_id=tutoria_id, horario_id=horario_asignado.id)
        db.session.add(nueva_inscripcion)

        # Cambiar el estado del horario a 'Ocupado'
        horario_asignado.estado = 'Ocupado'
        db.session.commit()

        flash("Inscripción realizada con éxito.", "success")
        return redirect(url_for('dashboard'))

    # Renderizar la página con la información de la tutoría y el horario asignado
    return render_template('inscripcion.html', tutoria=tutoria, docente=docente, horario=horario_asignado, docente_detalles=docente_detalles)

@app.route('/admin/gestionar_horarios', methods=['GET', 'POST'])
def gestionar_horarios():
    user = db.session.get(User, session['user_id'])  # Obtiene el usuario de la sesión
    
    # Verificar si el usuario es un administrador
    if not user or user.role != 'admin':
        flash("Acceso denegado. Solo los administradores pueden acceder a esta sección.", "danger")
        return redirect(url_for('dashboard'))
    
    if 'eliminar_horario' in request.form:
        horario_id = request.form['horario_id']
        horario = HorariosTutoria.query.get(horario_id)
        
        if horario:
            # Verificar si el horario tiene inscripciones asociadas
            inscripciones = Inscripcion.query.filter_by(horario_id=horario_id).all()
            if inscripciones:
                flash('No se puede eliminar un horario con inscripciones activas.', 'error')
            else:
                db.session.delete(horario)
                db.session.commit()
                flash('Horario eliminado correctamente.', 'success')
        else:
            flash('El horario no existe.', 'error')
            
    # Obtener todos los horarios con sus respectivas tutorías
    horarios = HorariosTutoria.query.all()
    
    # Obtener todas las tutorías creadas
    tutorias = Tutoria.query.all()  # Asegúrate de que esta consulta obtenga todas las tutorías disponibles

    if request.method == 'POST':
        # Verificar si la solicitud es para crear un nuevo horario
        if 'crear' in request.form:
            tutoria_id = request.form.get('tutoria_id')  # Tutoría seleccionada
            dia = request.form.get('dia')  # Día seleccionado
            hora = request.form.get('hora')  # Hora seleccionada
            estado = request.form.get('estado')  # Estado seleccionado
            
            # Validar que se haya seleccionado todos los campos
            if not tutoria_id or not dia or not hora or not estado:
                flash('Todos los campos son requeridos', 'danger')
                return render_template('gestionar_horarios.html', horarios=horarios, tutorias=tutorias)
            
            # Verificar si ya existe un horario para esa tutoría y día/hora
            existing_horario = HorariosTutoria.query.filter_by(tutoria_id=tutoria_id, dia=dia, hora=hora).first()
            if existing_horario:
                flash('Ya existe un horario asignado para esa tutoría en ese día y hora', 'danger')
                return render_template('gestionar_horarios.html', horarios=horarios, tutorias=tutorias)
            
            # Crear el nuevo horario
            nuevo_horario = HorariosTutoria(
                tutoria_id=tutoria_id,
                dia=dia,
                hora=hora,
                estado=estado
            )
            db.session.add(nuevo_horario)
            db.session.commit()
            
            flash('Nuevo horario creado con éxito', 'success')

        # Verificar si la solicitud es para cambiar el estado de un horario existente
        elif 'cambiar_estado' in request.form:
            horario_id = request.form.get('horario_id')  # ID del horario
            nuevo_estado = request.form.get('estado')  # Nuevo estado seleccionado
            
            # Buscar el horario en la base de datos
            horario = HorariosTutoria.query.get(horario_id)
            
            if not horario:
                flash('Horario no encontrado', 'danger')
            else:
                # Cambiar el estado del horario
                horario.estado = nuevo_estado
                db.session.commit()
                flash('Estado del horario actualizado con éxito', 'success')
    
        return redirect(url_for('gestionar_horarios'))  # Redirigir para refrescar la página con el nuevo estado o horario

    # Mostrar la vista con todos los horarios y formularios para crear nuevos
    return render_template('gestionar_horarios.html', horarios=horarios, tutorias=tutorias)

@app.route('/tutorias/disponibles', methods=['GET'])
def tutorias_disponibles():
    
    # Consulta todas las tutorías
    tutorias = Tutoria.query.all()
    
    # Mostrar mensaje sobre días festivos
    flash("Recuerda que no hay tutorías los días festivos.", "info")


    return render_template('tutoria_disponible.html', tutorias=tutorias)

@app.route('/teacher/tutorias-apartadas/<int:docente_id>', methods=['GET'])
def listar_tutorias_apartadas(docente_id):
    # Consultar tutorías del docente que tengan inscripciones
    
    tutorias_inscritas = (
        Inscripcion.query
        .join(Tutoria)  # Unir con la tabla de tutorías
        .join(HorariosTutoria)  # Unir con la tabla de horarios
        .filter(Tutoria.docente_id == docente_id)  # Filtrar por el docente
        .filter(
            (HorariosTutoria.estado != 'Disponible') & 
            (HorariosTutoria.estado != 'No disponible')
        )  # Solo mostrar horarios ocupados
        .distinct()  # Evitar duplicados
        .all()  # Obtener todos los resultados
    )

    return render_template('tutorias_programadas.html', tutorias=tutorias_inscritas, docente_id=docente_id)

@app.route('/student/tutorias-inscritas', methods=['GET'])
def listar_tutorias_inscritas():
    
    user = db.session.get(User, session['user_id'])
    
    if not user or user.role != 'student':
        flash("Acceso denegado. Solo los estudiantes pueden acceder a esta sección.", "danger")
        return redirect(url_for('dashboard'))


    # Consultar tutorías del estudiante que tengan inscripciones
    inscripciones = Inscripcion.query.filter_by(estudiante_id=user.id).all()
    
    return render_template('tutorias_inscritas.html', inscripciones=inscripciones)

@app.route('/student/tutorias-inscritas/eliminar/<int:inscripcion_id>', methods=['GET'])
def eliminar_inscripcion(inscripcion_id):
    try:
        # Obtener el usuario actual
        user = db.session.get(User, session.get('user_id'))
        
        if not user or user.role != 'student':
            flash("Acceso denegado. Solo los estudiantes pueden acceder a esta sección.", "danger")
            return redirect(url_for('dashboard'))
        
        # Buscar la inscripción por inscripcion_id
        inscripcion = Inscripcion.query.filter_by(id=inscripcion_id, estudiante_id=user.id).first()
        
        if inscripcion:
            # Eliminar la inscripción
            db.session.delete(inscripcion)
            db.session.commit()

            # Cambiar el estado del horario a 'Disponible'
            horario = HorariosTutoria.query.get(inscripcion.horario_id)
            if horario:
                horario.estado = 'Disponible'
                db.session.commit()
            
            flash('Inscripción eliminada exitosamente.', 'success')
        else:
            flash('Inscripción no encontrada.', 'danger')
    except Exception as e:
        db.session.rollback()  # Si ocurre un error, deshacer los cambios
        flash(f'Error al eliminar la inscripción: {str(e)}', 'danger')
    
    return redirect(url_for('listar_tutorias_inscritas'))

@app.route('/student/tutorias-inscritas/editar/<int:inscripcion_id>', methods=['GET', 'POST'])
def editar_inscripcion(inscripcion_id):
    # Obtener la inscripción actual
    inscripcion = Inscripcion.query.get(inscripcion_id)
    if not inscripcion:
        flash("La inscripción no existe.", "error")
        return redirect(url_for('ver_inscripciones'))

    # Obtener información actual: horario y materia
    horario_actual = inscripcion.horario
    materia = inscripcion.tutoria.espacio_academico

    if request.method == 'POST':
        # Obtener el nuevo horario desde el formulario
        nuevo_horario_id = request.form.get('nuevo_horario')

        # Si no seleccionó un nuevo horario, no hacer cambios
        if not nuevo_horario_id:
            flash("No se realizaron cambios a la inscripción.", "info")
            return redirect(url_for('listar_tutorias_inscritas'))

        # Obtener el horario seleccionado y validar
        nuevo_horario = HorariosTutoria.query.get(nuevo_horario_id)
        if not nuevo_horario or nuevo_horario.estado != 'Disponible':
            flash("El horario seleccionado no es válido o no está disponible.", "error")
            return redirect(url_for('editar_inscripcion', inscripcion_id=inscripcion_id))

        # Actualizar la inscripción
        inscripcion.horario_id = nuevo_horario.id
        db.session.commit()

        # Cambiar estado del horario
        nuevo_horario.estado = 'No disponible'
        horario_actual.estado = 'Disponible'  # Liberar el horario anterior
        db.session.commit()

        flash("Inscripción actualizada correctamente.", "success")
        return redirect(url_for('listar_tutorias_inscritas'))

    # Obtener horarios disponibles para la misma tutoría
    horarios_disponibles = HorariosTutoria.query.filter_by(
        tutoria_id=inscripcion.tutoria_id, estado='Disponible'
    ).all()

    return render_template(
        'edit_inscripcion.html',
        inscripcion=inscripcion,
        horario_actual=horario_actual,
        materia=materia,
        horarios_disponibles=horarios_disponibles
    )
    
@app.route('/formato_tutoria', methods=['GET', 'POST'])
@login_required
def formato_tutoria():
    if request.method == 'POST':
        # Capturar datos del formulario
        docente_id = request.form.get('docente')
        tutoria_id = request.form.get('tutoria')
        periodo_academico = request.form.get('periodo_academico')
        codigo = request.form.get('codigo')
        semestre = request.form.get('semestre')
        espacio_academico = request.form.get('espacio_academico')
        temas_tratados = request.form.get('temas_tratados') or None  # Opcional
        fecha_realizacion = request.form.get('fecha_realizacion')

        # Validar campos obligatorios
        if not all([docente_id,tutoria_id,periodo_academico,codigo,semestre,espacio_academico, temas_tratados,fecha_realizacion]):
            flash('Todos los campos obligatorios deben completarse.', 'danger')
            return redirect(url_for('formato_tutoria'))

        # Crear y guardar el nuevo formato
        nuevo_formato = FormatoTutoria(
            docente_id=int(docente_id),
             estudiante_id=current_user.id,
            tutoria_id=int(tutoria_id),
            periodo_academico=periodo_academico,
            codigo=codigo,
            semestre= semestre,
            espacio_academico=espacio_academico,
            temas_tratados=temas_tratados,
            fecha_realizacion=fecha_realizacion
        )
        db.session.add(nuevo_formato)
        db.session.commit()

        flash('Formato de tutoría guardado exitosamente.', 'success')
        return redirect(url_for('dashboard'))

    # Consultar datos para el formulario
    docentes = User.query.filter_by(role='teacher').all()
    estudiantes = User.query.filter_by(role='student').all()
    tutorias = Tutoria.query.all()

    return render_template('formato_tutoria.html', docentes=docentes, estudiantes=estudiantes, tutorias=tutorias)

@app.route('/listar_formato', methods=['GET'])
def listar_formato():
    # Obtener todos los formatos de tutoría
    formatos = FormatoTutoria.query.all()

    return render_template('listar_formato.html', formatos=formatos)

@app.route('/exportar_csv/<int:docente_id>', methods=['GET'])
def exportar_csv(docente_id):
    # Consultar tutorías del docente que tengan inscripciones
    tutorias_inscritas = (
        Inscripcion.query
        .join(Tutoria)  # Unir con la tabla de tutorías
        .join(HorariosTutoria)  # Unir con la tabla de horarios
        .filter(Tutoria.docente_id == docente_id)  # Filtrar por el docente
        .filter(
            (HorariosTutoria.estado != 'Disponible') & 
            (HorariosTutoria.estado != 'No disponible')
        )  # Solo mostrar horarios ocupados
        .distinct()  # Evitar duplicados
        .all()  # Obtener todos los resultados
    )
    
    # Verificar si la consulta devuelve datos
    if not tutorias_inscritas:
        print(f"No se encontraron tutorías para el docente con ID {docente_id}.")
        return "No hay tutorías inscritas para este docente."

    print(f"Se encontraron {len(tutorias_inscritas)} inscripciones.")
    for inscripcion in tutorias_inscritas:
        print(f"Estudiante: {inscripcion.estudiante.nombre_completo}, "
              f"Tutoria: {inscripcion.tutoria.codigo}, "
              f"Horario: {inscripcion.horario.dia} {inscripcion.horario.hora}, "
              f"Fecha Inscripción: {inscripcion.fecha_inscripcion}")

    # Crear el archivo CSV en memoria con StringIO
    output = io.StringIO()
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Escribir los encabezados de la tabla
    writer.writerow(['Estudiante', 'Tutoria', 'Horario', 'Fecha de Inscripción'])

    # Escribir los datos
    for inscripcion in tutorias_inscritas:
        estudiante_nombre = inscripcion.estudiante.nombre_completo
        tutoria_codigo = inscripcion.tutoria.codigo
        horario_info = f"{inscripcion.horario.dia} {inscripcion.horario.hora}"
        fecha_inscripcion = inscripcion.fecha_inscripcion.strftime('%Y-%m-%d %H:%M:%S')
        
        # Asegurarse de que estamos escribiendo en el archivo
        print(f"Escribiendo fila: {estudiante_nombre}, {tutoria_codigo}, {horario_info}, {fecha_inscripcion}")
        writer.writerow([estudiante_nombre, tutoria_codigo, horario_info, fecha_inscripcion])

    # Mover el cursor de la cadena al inicio antes de enviarlo
    output.seek(0)

    # Devolver el archivo CSV como respuesta
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), 
                     mimetype='text/csv', 
                     as_attachment=True, 
                     download_name='tutorias_programadas.csv')

@app.route('/exportar_pdf/<int:docente_id>', methods=['GET'])
def exportar_pdf(docente_id):
    # Consultar tutorías del docente que tengan inscripciones
    tutorias_inscritas = (
        Inscripcion.query
        .join(Tutoria)  # Unir con la tabla de tutorías
        .join(HorariosTutoria)  # Unir con la tabla de horarios
        .filter(Tutoria.docente_id == docente_id)  # Filtrar por el docente
        .filter(
            (HorariosTutoria.estado != 'Disponible') & 
            (HorariosTutoria.estado != 'No disponible')
        )  # Solo mostrar horarios ocupados
        .distinct()  # Evitar duplicados
        .all()  # Obtener todos los resultados
    )

    # Verificar si la consulta devuelve datos
    if not tutorias_inscritas:
        print(f"No se encontraron tutorías para el docente con ID {docente_id}.")
        return "No hay tutorías inscritas para este docente."

    print(f"Se encontraron {len(tutorias_inscritas)} inscripciones.")
    for inscripcion in tutorias_inscritas:
        print(f"Estudiante: {inscripcion.estudiante.nombre_completo}, "
              f"Tutoria: {inscripcion.tutoria.codigo}, "
              f"Horario: {inscripcion.horario.dia} {inscripcion.horario.hora}, "
              f"Fecha Inscripción: {inscripcion.fecha_inscripcion}")

    # Crear el archivo PDF en memoria
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    width, height = letter

    # Título del documento
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 40, "Inscripciones a Tutorías")

    # Configurar el contenido en el PDF
    y_position = height - 80
    c.setFont("Helvetica", 12)

    # Agregar los datos de las inscripciones
    for inscripcion in tutorias_inscritas:
        estudiante_nombre = inscripcion.estudiante.nombre_completo
        tutoria_codigo = inscripcion.tutoria.codigo
        horario_info = f"{inscripcion.horario.dia} {inscripcion.horario.hora}"
        fecha_inscripcion = inscripcion.fecha_inscripcion.strftime('%Y-%m-%d %H:%M:%S')

        # Escribir la fila
        c.drawString(100, y_position, f"Estudiante: {estudiante_nombre},")
        c.drawString(100, y_position - 20, f"Tutoria: {tutoria_codigo},")
        c.drawString(100, y_position - 40, f"Horario: {horario_info},")
        c.drawString(100, y_position - 60, f"Fecha Inscripción: {fecha_inscripcion}")
        y_position -= 80

        if y_position < 50:
            c.showPage()
            y_position = height - 40

    # Finalizar y guardar el PDF
    c.save()

    # Mover el puntero al principio del archivo para enviarlo
    output.seek(0)

    # Devolver el archivo PDF como respuesta
    return send_file(output, mimetype='application/pdf', as_attachment=True, download_name='tutorias_programadas.pdf')

if __name__ == '__main__':
    app.run(debug=True)  # Inicia la aplicación en modo debug

