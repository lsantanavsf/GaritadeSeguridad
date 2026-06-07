from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
import uuid
from . import models, schemas

# --- OPERACIONES PARA RESIDENTES ---

def crear_residente(db: Session, residente: schemas.ResidenteCreate, usuario_id: int = None):
    
    # Generar código único si no viene en el registro 
    cod_final = residente.codigo_unico if residente.codigo_unico else f"REG-{uuid.uuid4().hex[:4].upper()}"
    
    db_residente = models.Residente(
        nombre_propietario=residente.nombre_propietario,
        numero_casa=residente.numero_casa,
        codigo_unico=cod_final,
        correo_notificacion=residente.correo_notificacion,
        usuario_id=usuario_id        # conexión con la tabla usuarios
    )
    db.add(db_residente)
    db.commit()
    db.refresh(db_residente)
    return db_residente

def obtener_residentes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Residente).offset(skip).limit(limit).all()

def obtener_residente_por_codigo(db: Session, codigo: str):
    return db.query(models.Residente).filter(
        or_(
            models.Residente.numero_casa == codigo,
            models.Residente.codigo_unico == codigo
        )
    ).first()

# --- OPERACIONES PARA USUARIOS ---


def crear_usuario(db: Session, usuario: schemas.UsuarioCreate):
    db_usuario = models.Usuario(
        username=usuario.username,
        password_hash=usuario.password, # En el futuro usaremos passlib para hashing
        rol=usuario.rol
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

# --- OPERACIONES PARA CONTROL DE ACCESOS (GUARDIA) ---

def registrar_entrada(db: Session, acceso: schemas.AccesoCreate):

    # 1. Registramos al visitante 
    nuevo_visitante = models.Visitante(
        nombre_completo=acceso.nombre_visitante,
        placa_vehiculo=acceso.placa_vehiculo
    )
    db.add(nuevo_visitante)
    db.commit()
    db.refresh(nuevo_visitante)

    # 2. Registramos el acceso vinculando las identidades
    db_acceso = models.Acceso(
        visitante_id=nuevo_visitante.id,
        residente_id=acceso.residente_id,
        tipo_acceso=acceso.tipo_acceso
    )
    db.add(db_acceso)
    db.commit()
    db.refresh(db_acceso)
    
    # Inyectamos datos para el frontend antes de retornar
    db_acceso.nombre_visitante = nuevo_visitante.nombre_completo
    db_acceso.placa_vehiculo = nuevo_visitante.placa_vehiculo
    return db_acceso

def registrar_salida(db: Session, acceso_id: int):
    db_acceso = db.query(models.Acceso).filter(models.Acceso.id == acceso_id).first()
    if db_acceso:
        db_acceso.fecha_salida = datetime.now()
        db.commit()
        db.refresh(db_acceso)
    return db_acceso

def obtener_accesos_activos(db: Session):
    
    # Gracias a las relationships en models.py, SQLAlchemy trae al visitante automáticamente
    accesos = db.query(models.Acceso).filter(models.Acceso.fecha_salida == None).all()
    for a in accesos:
        if a.visitante:
            a.nombre_visitante = a.visitante.nombre_completo
            a.placa_vehiculo = a.visitante.placa_vehiculo
    return accesos

def obtener_historial_accesos(db: Session, limit: int = 20):
    historial = db.query(models.Acceso).filter(
        models.Acceso.fecha_salida != None
    ).order_by(models.Acceso.fecha_salida.desc()).limit(limit).all()
    
    for a in historial:
        if a.visitante:
            a.nombre_visitante = a.visitante.nombre_completo
            a.placa_vehiculo = a.visitante.placa_vehiculo
    return historial