-- Tabla de tutorías
CREATE TABLE tutoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE, -- Código único para la tutoría
    espacio_academico VARCHAR(100) NOT NULL, -- Nombre del espacio académico
    docente_id INT, -- Relación con el docente
    FOREIGN KEY (docente_id) REFERENCES user(id) -- Clave foránea al usuario
);

-- Tabla de estudiantes
CREATE TABLE estudiante (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE, -- Código único para el estudiante
    semestre VARCHAR(20), -- Semestre académico
    programa_academico VARCHAR(100), -- Programa al que pertenece
    estudiante_id INT NOT NULL, -- Relación con la tabla user
    estado ENUM('Activo', 'Inactivo', 'Graduado') DEFAULT 'Activo', -- Estado del estudiante
    FOREIGN KEY (estudiante_id) REFERENCES user(id) ON DELETE CASCADE -- Eliminar en cascada
);

-- Tabla de docentes
CREATE TABLE docente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    departamento VARCHAR(100), -- Departamento académico del docente
    correo_institucional VARCHAR(100) NOT NULL UNIQUE, -- Correo institucional único
    fecha_ingreso DATE NOT NULL, -- Fecha de ingreso del docente
    docente_id INT NOT NULL, -- Relación con la tabla user
    FOREIGN KEY (docente_id) REFERENCES user(id) ON DELETE CASCADE -- Eliminar en cascada
);

-- Tabla de horarios de tutorías
CREATE TABLE horarios_tutoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tutoria_id INT NOT NULL, -- Relación con la tutoría
    dia ENUM('Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes') NOT NULL, -- Día de la tutoría
    hora ENUM(
        '08:00 AM - 09:00 AM',
        '09:00 AM - 10:00 AM',
        '10:00 AM - 11:00 AM',
        '11:00 AM - 12:00 PM',
        '01:00 PM - 02:00 PM',
        '02:00 PM - 03:00 PM',
        '03:00 PM - 04:00 PM',
        '04:00 PM - 05:00 PM'
    ) NOT NULL,
    estado ENUM('Disponible', 'No disponible', 'Ocupado') NOT NULL, -- Estado del horario
    FOREIGN KEY (tutoria_id) REFERENCES tutoria(id) ON DELETE CASCADE -- Eliminar en cascada
);

-- Tabla de inscripciones
CREATE TABLE inscripcion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estudiante_id INT NOT NULL, -- Relación con el estudiante
    tutoria_id INT NOT NULL, -- Relación con la tutoría
    horario_id INT NOT NULL, -- Relación con el horario de la tutoría
    fecha_inscripcion DATETIME NOT NULL, -- Fecha y hora de la inscripción
    FOREIGN KEY (estudiante_id) REFERENCES user(id) ON DELETE CASCADE, -- Eliminar en cascada
    FOREIGN KEY (tutoria_id) REFERENCES tutoria(id) ON DELETE CASCADE, -- Eliminar en cascada
    FOREIGN KEY (horario_id) REFERENCES horarios_tutoria(id) ON DELETE CASCADE -- Eliminar en cascada
);

-- Tabla de formato de tutoría
CREATE TABLE formato_tutoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tutoria_id INT NOT NULL,  -- Relación con la tutoría
    docente_id INT NOT NULL,  -- Relación con el docente
    estudiante_id INT NOT NULL,  -- Relación con el estudiante
    periodo_academico VARCHAR(50) NOT NULL,  -- Periodo académico
    codigo_estudiante VARCHAR(20) NOT NULL,  -- Código del estudiante
    semestre_estudiante VARCHAR(20) NOT NULL,  -- Semestre del estudiante
    espacio_academico VARCHAR(100) NOT NULL,  -- Espacio académico
    temas_tratados TEXT,  -- Temas tratados
    fecha DATE NOT NULL,  -- Fecha de realización
    FOREIGN KEY (tutoria_id) REFERENCES tutoria(id) ON DELETE CASCADE,
    FOREIGN KEY (docente_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (estudiante_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Tabla de compromisos
CREATE TABLE compromiso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descripcion TEXT NOT NULL  -- Descripción del compromiso
);

-- Tabla de relación entre formato de tutoría y compromisos
CREATE TABLE formato_tutoria_compromiso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    formato_tutoria_id INT NOT NULL,  -- Relación con el formato de tutoría
    compromiso_id INT NOT NULL,  -- Relación con el compromiso
    FOREIGN KEY (formato_tutoria_id) REFERENCES formato_tutoria(id) ON DELETE CASCADE,
    FOREIGN KEY (compromiso_id) REFERENCES compromiso(id) ON DELETE CASCADE
);

pip install Flask
pip install Flask-Bcrypt
pip install Flask-SQLAlchemy
pip install Flask-Session

# Integrantes proyecto:

Karoll Catalina Amaya Casallas
Vanesa Alexandra Amaya Bohorquez
Laura Yulieth López Albino
Maria Camila Lopez Bernal 

# Tablas extras:

La tabla de estudiante guarda información adicional referente al estudiante con el fin de que sea más completa y se pueda usar esta información en tutorias.

La tabla docente funciona de manera similar a la de estudiante sino con menos campos

La tabla horario_tutoria todavía no esta en uso, es un planteamiento para poder más adelante guardar horarios que se asigen por tutoria.

# contexto de los paquetes:

Flask: Este es el framework para construir la aplicación web.
Flask-Bcrypt: Esta extensión proporciona hashing de contraseñas utilizando Bcrypt.
Flask-SQLAlchemy: Este es un ORM (Object Relational Mapper) que facilita la interacción con bases de datos SQL.
Flask-Session: Esta extensión permite gestionar sesiones en la aplicación Flask.

# relación de endpoints:

/: Redirige al usuario a la página de inicio de sesión o al panel de control según su rol si ya está autenticado.

/login: Maneja el inicio de sesión de usuarios. Si se envían credenciales válidas, redirige al panel de control; si no, muestra un mensaje de error.

/register: Permite a nuevos usuarios registrarse. Verifica la unicidad del nombre de usuario y la identificación antes de crear un nuevo usuario. Además, por cada tipo de rol que se registre (estudiante o docente) apareceran campos extras para llenar que se almacenaran en tablas auxiliares

/dashboard: Muestra el panel de control del usuario. Requiere que el usuario esté autenticado.

/logout: Cierra la sesión del usuario y redirige a la página de inicio de sesión.

/admin/users: Permite a los administradores gestionar usuarios (ver, eliminar). Solo accesible para usuarios con rol de administrador. Elimina los usuarios junto con la información respectiva en las tablas auxiliares(docente y estudiante) ejemplo, elimino un usuario con rol docente este también se eliminara de la tabla docente

/student_profile: Permite a los estudiantes ver a detalle los datos de su perfil sin necesidad de editarlo.

/teacher_profile: Permite a los docentes ver a detalle los datos de sus perfil sin necesidad de editarlo.

/admin/users/edit/<int:user_id>: Permite a los administradores editar la información de un usuario específico, incluyendo los campos de las tablas docente o estudiante según sea el rol.

/admin/users/detalle_user/<int:user_id>:Muestra los detalles de los usuarios sin necesidad de editarlos

/admin/tutorias: Permite a los administradores gestionar tutorías (crear, listar). Solo accesible para usuarios con rol de administrador. Se incluye genenar el codigo de la tutoria de manera automatica a partir del nombre de la tutoria

/admin/tutorias/delete/<int:tutoria_id>: Elimina una tutoría específica. Solo accesible para usuarios con rol de administrador.

/admin/tutorias/edit/<int:tutoria_id>: Permite a los administradores editar los detalles de una tutoría específica.

/profile/edit: Permite a los usuarios editar su perfil (nombre de usuario, identificación, contraseña). Requiere autenticación. 
