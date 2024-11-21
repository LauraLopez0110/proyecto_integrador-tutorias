from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_bcrypt import Bcrypt
from config import Config
from models import db, User,Tutoria, Estudiante, Docente, HorariosTutoria
from models import Inscripcion,FormatoTutoria, Compromiso, FormatoTutoriaCompromiso
# Importa db y User, Tutoria
from datetime import datetime


app = Flask(__name__)
app.config.from_object(Config)  # Carga la configuración desde el objeto Config
db.init_app(app)  # Inicializa la base de datos con la app
bcrypt = Bcrypt(app)  # Inicializa Flask-Bcrypt para manejar el hash de contraseñas

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



@app.route('/teacher/<int:docente_id>/tutorias', methods=['GET'])
def listar_tutorias_por_docente(docente_id):
    
    user = db.session.get(User, session['user_id'])  # Obtiene el usuario de la sesión
    # Verificar si el docente existe y si tiene el rol 'teacher'
    docente = User.query.filter_by(id=docente_id, role='teacher').first()  # Asegúrate que el usuario tenga el rol 'teacher'
    if not docente:
        flash("Docente no encontrado", "danger")
        return redirect(url_for('dashboard'))  # Redirigir si no se encuentra el docente

    # Obtener las tutorías del docente
    tutorias = Tutoria.query.filter_by(docente_id=docente_id).all()

    # Renderizar la plantilla con la lista de tutorías
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
            flash('Debe seleccionar tanto el día como la hora', 'error')
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
    
    # Filtrar horarios sin inscripciones (disponibles)
    horarios_tutorias = HorariosTutoria.query.filter(
        HorariosTutoria.tutoria_id == tutoria_id, 
        ~HorariosTutoria.inscripciones.any()  # Esto filtra los horarios sin inscripciones
    ).all()

    if request.method == 'POST':
        horario_id = request.form.get('horario')
        
        if not horario_id:
            flash("Debe seleccionar un horario.", "danger")
            return render_template('inscripcion.html', tutoria=tutoria, horarios=horarios_tutorias)
        
        horario = HorariosTutoria.query.get(horario_id)
        if not horario or horario.inscripciones:
            flash("El horario seleccionado ya no está disponible.", "danger")
            return redirect(url_for('inscribirse_tutoria', tutoria_id=tutoria_id))
        
        # Verificar si el estudiante ya está inscrito en esta tutoría
        inscripcion_existente = Inscripcion.query.filter_by(estudiante_id=user.id, tutoria_id=tutoria_id).first()
        if inscripcion_existente:
            flash("Ya estás inscrito en esta tutoría.", "warning")
            return redirect(url_for('dashboard'))

        # Crear inscripción
        nueva_inscripcion = Inscripcion(estudiante_id=user.id, tutoria_id=tutoria_id, horario_id=horario_id)

        db.session.add(nueva_inscripcion)
        db.session.commit()

        flash("Inscripción realizada con éxito.", "success")
        return redirect(url_for('dashboard'))
    
    return render_template('inscripcion.html', tutoria=tutoria, horarios=horarios_tutorias)

@app.route('/tutorias/disponibles', methods=['GET'])
def tutorias_disponibles():
    
    # Consulta todas las tutorías
    tutorias = Tutoria.query.all()
    

    return render_template('tutoria_disponible.html', tutorias=tutorias)

@app.route('/teacher/tutorias-apartadas/<int:docente_id>', methods=['GET'])
def listar_tutorias_apartadas(docente_id):
    # Consultar tutorías del docente que tengan inscripciones
    
    
    tutorias_inscritas = (
        Tutoria.query
        .filter(
            Tutoria.docente_id == docente_id,  # Filtrar por docente
        )
        .join(Inscripcion)  # Solo tutorías con inscripciones
        .distinct()
        .all()
             
    )

    return render_template('tutorias_apartadas.html', tutorias=tutorias_inscritas)
if __name__ == '__main__':
    app.run(debug=True)  # Inicia la aplicación en modo debug

