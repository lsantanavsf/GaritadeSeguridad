from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Credenciales (Asegúrate que el nombre de la BD coincida con el que creaste)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234@localhost:5432/garita_db"

# 2. Motor de conexión con "Pool Pre-Ping"
# Esto verifica si la conexión sigue viva antes de usarla, evitando errores de "Connection Lost"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Toque de ciberseguridad: evita ataques de denegación por conexiones muertas
    pool_size=5,         # Limita el número de conexiones simultáneas
    max_overflow=10
)

# 3. Configuración de sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Clase Base
Base = declarative_base()

# 5. Dependencia de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()