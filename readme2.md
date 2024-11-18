CREATE TABLE tutoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,  -- Código único para la tutoría
    espacio_academico VARCHAR(100) NOT NULL,
    docente_id INT,
    FOREIGN KEY (docente_id) REFERENCES user(id)  -- Relación con la tabla user
);

CREATE TABLE estudiante (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE, -- Código único por estudiante
    semestre VARCHAR(20),
    programa_academico VARCHAR(100),
    estudiante_id INT, -- Referencia a la tabla user
    estado ENUM('Activo', 'Inactivo', 'Graduado') DEFAULT 'Activo', -- Campo de estado
    FOREIGN KEY (estudiante_id) REFERENCES user(id) ON DELETE CASCADE -- Relación con la tabla user, con eliminación en cascada
);

CREATE TABLE docente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    departamento VARCHAR(100),
    correo_institucional VARCHAR(100) NOT NULL UNIQUE, -- Correo institucional
    fecha_ingreso DATE, -- Fecha de ingreso a la universidad
    docente_id INT,
    FOREIGN KEY (docente_id) REFERENCES user(id) ON DELETE CASCADE -- Relación con la tabla user, con eliminación en cascada
);

CREATE TABLE horarios_tutoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tutoria_id INT NOT NULL,
    dia ENUM('Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes') NOT NULL,
    hora ENUM('8:00-9:00', '9:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00') NOT NULL,
    estado ENUM('Disponible', 'No disponible') NOT NULL,
    FOREIGN KEY (tutoria_id) REFERENCES tutoria(id) ON DELETE CASCADE
);

CREATE TABLE inscripcion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estudiante_id INT NOT NULL,
    tutoria_id INT NOT NULL,
    horario_id INT NOT NULL,
    fecha_inscripcion DATETIME NOT NULL,  -- Cambié a DATETIME
    FOREIGN KEY (estudiante_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (tutoria_id) REFERENCES tutoria(id) ON DELETE CASCADE,
    FOREIGN KEY (horario_id) REFERENCES horarios_tutoria(id) ON DELETE CASCADE  -- Cambié el nombre de la tabla
);

CREATE TABLE formato_tutoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    docente_id INT NOT NULL,
    estudiante_id INT NOT NULL,
    tutoria_id INT NOT NULL,
    espacio_academico VARCHAR(100) NOT NULL,
    temas_tratados TEXT NOT NULL,
    fecha DATE NOT NULL,
    FOREIGN KEY (docente_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (estudiante_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (tutoria_id) REFERENCES tutoria(id) ON DELETE CASCADE
);

CREATE TABLE compromiso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descripcion TEXT NOT NULL -- Descripción del compromiso predefinido
);

CREATE TABLE formato_tutoria_compromiso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    formato_tutoria_id INT NOT NULL,
    compromiso_id INT NOT NULL,
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
