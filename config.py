import os  # Importa el módulo os para interactuar con el sistema operativo

class Config:
  
    SECRET_KEY = os.environ.get('USTA_2024') or 'usta_2024'  
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:@localhost/users_db'  
    SQLALCHEMY_TRACK_MODIFICATIONS = False  
