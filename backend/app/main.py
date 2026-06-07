from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import qrcode
from io import BytesIO
import uuid 

# Importaciones locales
from . import crud, models, schemas, email_service
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Garita Tecnológica API",
    description="Sistema de control de acceso para residenciales con IAM y Notificaciones",
    version="0.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", tags=["General"])
def inicio():
    return {"mensaje": "Bienvenido al Sistema de Garita Tecnológica"}

# --- SECCIÓN SEGURIDAD Y USUARIOS (IAM) ---

@app.post("/usuarios/", response_model=schemas.Usuario, tags=["Seguridad"])
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    return crud.crear_usuario(db=db, usuario=usuario)

# NUEVA RUTA CRUCIAL: Necesaria para que el frontend liste tus agentes ("Tigre@fiel.com", etc.)
@app.get("/usuarios/", response_model=List[schemas.Usuario], tags=["Seguridad"])
def leer_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).offset(skip).limit(limit).all()
    return usuarios

@app.post("/login", tags=["Seguridad"])
def login(datos: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.username == datos.username).first()
    
    if not user or user.password_hash != datos.password:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    residente_id = None
    if user.rol == "vecino":
        residente = db.query(models.Residente).filter(models.Residente.usuario_id == user.id).first()
        if residente:
            residente_id = residente.id

    return {
        "id": user.id,
        "username": user.username,
        "rol": user.rol,
        "residente_id": residente_id
    }

# --- SECCIÓN RESIDENTES & QR ---

@app.post("/residentes/", response_model=schemas.Residente, tags=["Residentes"])
def registrar_residente(residente: schemas.ResidenteCreate, db: Session = Depends(get_db)):
    existe_usuario = db.query(models.Usuario).filter(models.Usuario.username == residente.correo_notificacion).first()
    if existe_usuario:
        raise HTTPException(status_code=400, detail="El correo ya está registrado como usuario")

    try:
        # 1. Crear el usuario de login con credenciales automáticas
        nuevo_usuario_data = schemas.UsuarioCreate(
            username=residente.correo_notificacion,
            password=residente.numero_casa, 
            rol="vecino"
        )
        nuevo_usuario = crud.crear_usuario(db=db, usuario=nuevo_usuario_data)

        # 2. Guardar el residente asociado en PostgreSQL
        db_residente = crud.crear_residente(db=db, residente=residente, usuario_id=nuevo_usuario.id)
        
        # 3. NOTIFICACIÓN AUTOMÁTICA (Envío de correo de bienvenida)
        email_service.enviar_correo_bienvenida(
            destinatario=residente.correo_notificacion,
            nombre_residente=residente.nombre_propietario,
            username=residente.correo_notificacion,
            password=residente.numero_casa
        )

        return db_residente
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al vincular identidad: {str(e)}")

@app.get("/residentes/", response_model=List[schemas.Residente], tags=["Residentes"])
def leer_residentes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_residentes(db, skip=skip, limit=limit)

@app.get("/residentes/qr/{id_residente}", tags=["Residentes"])
def obtener_qr_residente(id_residente: int, db: Session = Depends(get_db)):
    try:
        residente = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
        if not residente:
            raise HTTPException(status_code=404, detail="Residente no encontrado")

        contenido_qr = residente.codigo_unico
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(contenido_qr)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        return StreamingResponse(buf, media_type="image/png")
    
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=f"Error al generar QR: {str(e)}")

# --- SECCIÓN GUARDIA, INVITACIONES & ACCESOS ---

@app.get("/accesos/", tags=["Guardia"])
def obtener_todos_los_accesos(db: Session = Depends(get_db)):
    resultados = db.query(models.Acceso).all()
    lista_plana = []
    for r in resultados:
        lista_plana.append({
            "id": r.id,
            "residente_id": r.residente_id,
            "agente_id": r.agente_id, # Añadido para consistencia analítica
            "nombre_visitante": r.visitante.nombre_completo if r.visitante else "Desconocido",
            "placa_vehiculo": r.visitante.placa_vehiculo if r.visitante else "A pie",
            "fecha_entrada": r.fecha_entrada,
            "fecha_salida": r.fecha_salida,
            "tipo_acceso": r.tipo_acceso
        })
    return lista_plana

@app.post("/accesos/", tags=["Residentes"])
def procesar_invitacion_desde_vecino(payload: dict, db: Session = Depends(get_db)):
    residente_id = payload.get("residente_id")
    nombre_visitante = payload.get("nombre_visitante")
    placa = payload.get("placa_vehiculo")
    correo_invitado = payload.get("correo_invitado")

    residente = db.query(models.Residente).filter(models.Residente.id == residente_id).first()
    if not residente:
        raise HTTPException(status_code=404, detail="Residente inválido")

    try:
        # 1. Registrar Visitante en DB
        nuevo_visitante = models.Visitante(
            nombre_completo=nombre_visitante,
            placa_vehiculo=placa
        )
        db.add(nuevo_visitante)
        db.commit()
        db.refresh(nuevo_visitante)

        # 2. Crear Token Único
        token_seguridad = f"INV-{uuid.uuid4().hex[:6].upper()}-{residente.numero_casa}"

        # 3. Registrar acceso en estado Pendiente
        nuevo_acceso = models.Acceso(
            visitante_id=nuevo_visitante.id,
            residente_id=residente.id,
            tipo_acceso="QR",
            fecha_entrada=None  
        )
        db.add(nuevo_acceso)
        db.commit()

        # 4. Enviar el QR por correo
        email_service.enviar_correo_con_qr(
            destinatario=correo_invitado,  
            token=token_seguridad,
            nombre_residente=residente.nombre_propietario,
            casa=residente.numero_casa,
            nombre_invitado=nombre_visitante
        )

        return {"status": "success", "token_generado": token_seguridad}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Fallo del ecosistema: {str(e)}")

# Se asocia el response_model correcto para el filtro relacional de Pydantic
@app.post("/accesos/entrada", response_model=schemas.Acceso, tags=["Guardia"])
def registrar_ingreso(acceso: schemas.AccesoCreate, db: Session = Depends(get_db)):
    nuevo_acceso = crud.registrar_entrada(db=db, acceso=acceso)
    residente = db.query(models.Residente).filter(models.Residente.id == acceso.residente_id).first()
    
    if residente and residente.correo_notificacion:
        email_service.enviar_notificacion_visita(
            destinatario=residente.correo_notificacion,
            nombre_visitante=acceso.nombre_visitante, # Cambiado por dinamismo real de la alerta
            num_casa=residente.numero_casa
        )
    return nuevo_acceso

@app.put("/accesos/salida/{acceso_id}", tags=["Guardia"])
def registrar_salida_visitante(acceso_id: int, db: Session = Depends(get_db)):
    acceso = crud.registrar_salida(db, acceso_id=acceso_id)
    if not acceso:
        raise HTTPException(status_code=404, detail="El registro de acceso no existe")
    return {"mensaje": "Salida registrada con éxito", "fecha_salida": acceso.fecha_salida}

# --- SECCIÓN DASHBOARD (Estadísticas en tiempo real) ---

@app.get("/dashboard/stats", tags=["Dashboard"])
def obtener_metricas_dashboard(db: Session = Depends(get_db)):
    total_residentes = db.query(models.Residente).count()
    visitas_dentro = db.query(models.Acceso).filter(models.Acceso.fecha_entrada != None, models.Acceso.fecha_salida == None).count()
    total_usuarios = db.query(models.Usuario).count()

    return {
        "residentes_totales": total_residentes,
        "visitas_activas": visitas_dentro,
        "alertas_seguridad": 0  
    }