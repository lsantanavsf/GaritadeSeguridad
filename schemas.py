from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- ESQUEMAS DE USUARIOS (Login/IAM) ---
class UsuarioBase(BaseModel):
    username: str
    rol: str # 'admin', 'agente', 'vecino'

class UsuarioCreate(UsuarioBase):
    password: str

class Usuario(UsuarioBase):
    id: int
    
    
    # si el usuario no tiene un residente asignado (como los agentes de garita o el admin)
    residente_id: Optional[int] = None 

    class Config:
        from_attributes = True

        orm_mode = True

# --- ESQUEMAS DE RESIDENTES ---
class ResidenteBase(BaseModel):
    nombre_propietario: str
    numero_casa: str
    correo_notificacion: EmailStr # Valida formato automáticamente (ej. nombre@correo.com)

class ResidenteCreate(ResidenteBase):
    codigo_unico: Optional[str] = None 
    usuario_id: Optional[int] = None

class Residente(ResidenteBase):
    id: int
    codigo_unico: str
    usuario_id: Optional[int] = None 
    
    class Config:
        from_attributes = True
        orm_mode = True

# --- ESQUEMAS PARA VISITANTES ---
class VisitanteBase(BaseModel):
    nombre_completo: str
    dpi_licencia: Optional[str] = None
    placa_vehiculo: Optional[str] = None

class VisitanteCreate(VisitanteBase):
    pass

class Visitante(VisitanteBase):
    id: int
    
    class Config:
        from_attributes = True
        orm_mode = True

# --- ESQUEMAS PARA CONTROL DE ACCESOS ---
class AccesoCreate(BaseModel):
    nombre_visitante: str 
    placa_vehiculo: Optional[str] = None
    residente_id: int 
    tipo_acceso: str = "MANUAL" 

class Acceso(BaseModel):
    id: int
    visitante_id: int
    residente_id: int
    agente_id: Optional[int] = None  
    fecha_entrada: datetime
    fecha_salida: Optional[datetime] = None
    tipo_acceso: str
    nombre_visitante: Optional[str] = None 
    placa_vehiculo: Optional[str] = None

    class Config:  
        from_attributes = True
        orm_mode = True