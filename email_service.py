import smtplib
import qrcode
from io import BytesIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
# HERRAMIENTA CLAVE: Para dar formato correcto al remitente sin duplicados
from email.utils import formataddr

# --- CONFIGURACIÓN GLOBAL SMTP ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "santanavillalta0@gmail.com"  
SENDER_PASSWORD = "qfui rifn prde bvhl" 

def enviar_correo_bienvenida(destinatario: str, nombre_residente: str, username: str, password: str):
    """ Envia un correo electrónico corporativo al residente con sus accesos IAM """
    msg = MIMEMultipart()
    
    # CORRECCIÓN AQUÍ: formataddr empaqueta limpiamente ("Nombre", "Correo")
    msg['From'] = formataddr(("Sistema Garita Tecnológica", SENDER_EMAIL))
    msg['To'] = destinatario
    msg['Subject'] = "Bienvenido al Sistema de Control Residencial - Credenciales Activas"

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #2c3e50; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px; background-color: #ffffff;">
                <h2 style="color: #3498db; text-align: center;">¡Bienvenido a Residenciales Tec!</h2>
                <p>Hola <strong>{nombre_residente}</strong>,</p>
                <p>Tu cuenta de acceso al portal de residentes ha sido dada de alta exitosamente por la administración. A partir de ahora podrás controlar tus visitas y ver tus códigos de acceso en tiempo real.</p>
                
                <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db; margin: 20px 0;">
                    <p style="margin: 0 0 10px 0;"><strong>Tus Credenciales de Ingreso:</strong></p>
                    <p style="margin: 0;">📧 <strong>Usuario:</strong> {username}</p>
                    <p style="margin: 0;">🔑 <strong>Contraseña Temporal:</strong> {password}</p>
                </div>

                <p style="font-size: 0.9rem; color: #7f8c8d;">Nota de Seguridad: Tu contraseña inicial coincide con tu número de casa. Te sugerimos actualizarla al ingresar al sistema por primera vez.</p>
                <hr style="border: 0; border-top: 1px solid #edf2f7; margin: 20px 0;">
                <p style="text-align: center; font-size: 0.8rem; color: #a0aec0;">Sistema de Seguridad Inalámbrica - Garita Tecnológica Blue Team</p>
            </div>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f" Correo de bienvenida enviado a {destinatario}")
        return True
    except Exception as e:
        print(f"❌ Error al enviar bienvenida: {e}")
        return False

def enviar_notificacion_visita(destinatario: str, nombre_visitante: str, num_casa: str):
    """ Notifica al residente cuando su visita ha cruzado la garita física """
    msg = MIMEMultipart()
    
    # CORRECCIÓN AQUÍ: formataddr empaqueta limpiamente ("Nombre", "Correo")
    msg['From'] = formataddr(("Sistema Garita Tecnológica", SENDER_EMAIL))
    msg['To'] = destinatario
    msg['Subject'] = f"Aviso de Seguridad: Nueva Visita en Casa {num_casa}"

    cuerpo = f"""
    Estimado Residente,
    
    Se informa que se ha registrado el ingreso de una visita en la garita residencial:
    
    - Visitante: {nombre_visitante}
    - Destino: Casa {num_casa}
    - Estado: Ingreso Autorizado

    Este es un mensaje automático del Sistema de Garita Tecnológica.
    """
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() 
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Error al enviar notificación de visita: {e}")
        return False

def enviar_correo_con_qr(destinatario: str, token: str, nombre_residente: str, casa: str, nombre_invitado: str):
    """ Genera y envía una plantilla HTML limpia con el código QR incrustado directamente """
    msg = MIMEMultipart()
    
    # CORRECCIÓN AQUÍ: formataddr empaqueta limpiamente ("Nombre", "Correo")
    msg['From'] = formataddr(("Sistema Garita Tecnológica", SENDER_EMAIL))
    msg['To'] = destinatario
    msg['Subject'] = f"Pase de Acceso Autorizado - Casa {casa}"

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #2c3e50; text-align: center;">
            <div style="max-width: 500px; margin: 0 auto; padding: 25px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #fafbfe;">
                <h2 style="color: #27ae60; margin: 0;">Pase de Invitación</h2>
                <p style="color: #7f8c8d; font-size: 0.9rem;">Control de Accesos Automatizado</p>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 15px 0;">
                
                <p style="text-align: left;">Hola <strong>{nombre_invitado}</strong>,</p>
                <p style="text-align: left;">Te han generado un pase digital para ingresar a la residencia de <strong>{nombre_residente}</strong> en la <strong>Casa {casa}</strong>.</p>
                
                <p style="margin: 25px 0 10px 0; font-weight: bold; color: #1a252f;">MUESTRA ESTE QR EN LA ENTRADA PRINCIPAL:</p>
                <div style="background: white; padding: 15px; display: inline-block; border-radius: 10px; border: 1px solid #e2e8f0;">
                    <img src="cid:qr_code" style="width: 200px; height: 200px;" />
                </div>
                
                <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 15px;">Token de Auditoría: {token}</p>
                <p style="font-size: 0.85rem; background: #e8f5e9; color: #2e7d32; padding: 10px; border-radius: 6px; font-weight: bold;">Un solo uso válido.</p>
            </div>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(token)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        image_attachment = MIMEImage(buffer.getvalue())
        image_attachment.add_header('Content-ID', '<qr_code>')
        image_attachment.add_header('Content-Disposition', 'inline', filename="codigo_acceso.png")
        msg.attach(image_attachment)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Error al enviar QR: {e}")
        return False