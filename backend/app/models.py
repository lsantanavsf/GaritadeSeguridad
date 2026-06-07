from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(String) # 'admin', 'agente', 'vecino'

    # Relación inversa: Un usuario puede tener un perfil de residente
    residente = relationship("Residente", back_populates="usuario", uselist=False)
    
    # NUEVA RELACIÓN: Permite saber qué accesos ha procesado este agente (Trazabilidad)
    accesos_autorizados = relationship("Acceso", back_populates="agente")

class Residente(Base):
    __tablename__ = "residentes"
    id = Column(Integer, primary_key=True, index=True)
    nombre_propietario = Column(String, nullable=False)
    numero_casa = Column(String, unique=True, nullable=False)
    codigo_unico = Column(String, unique=True, nullable=False)
    correo_notificacion = Column(String, nullable=False)
    
    # Vinculación con Usuarios (IAM)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="residente")
    accesos = relationship("Acceso", back_populates="residente")

class Visitante(Base):
    __tablename__ = "visitantes"
    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String, nullable=False)
    dpi_licencia = Column(String)
    placa_vehiculo = Column(String)
    
    # Relación
    accesos = relationship("Acceso", back_populates="visitante")

class Acceso(Base):
    __tablename__ = "accesos"
    id = Column(Integer, primary_key=True, index=True)
    visitante_id = Column(Integer, ForeignKey("visitantes.id"))
    residente_id = Column(Integer, ForeignKey("residentes.id"))
    agente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    fecha_entrada = Column(DateTime, server_default=func.now())
    fecha_salida = Column(DateTime, nullable=True)
    tipo_acceso = Column(String) # 'MANUAL' o 'QR'
    
    # Relaciones completas y mapeadas
    visitante = relationship("Visitante", back_populates="accesos")
    residente = relationship("Residente", back_populates="accesos")
    
    # NUEVA RELACIÓN: Mapea la clave foránea agente_id de forma limpia
    agente = relationship("Usuario", back_populates="accesos_autorizados")