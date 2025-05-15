import requests
import json
from twilio.rest import Client
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env en desarrollo local
if os.path.exists('.env'):
    load_dotenv()

# Cargar claves desde variables de entorno
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TO_WHATSAPP = os.getenv("TO_WHATSAPP")
TWILIO_TEMPLATE_SID = os.getenv("TWILIO_TEMPLATE_SID")
SITE_URL = os.getenv("SITE_URL", "http://localhost")
SITE_NAME = os.getenv("SITE_NAME", "Morning Startup")

# Verificar variables requeridas
required_vars = {
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
    "TWILIO_SID": TWILIO_SID,
    "TWILIO_AUTH_TOKEN": TWILIO_AUTH_TOKEN,
    "TO_WHATSAPP": TO_WHATSAPP
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    raise EnvironmentError(f"Faltan las siguientes variables de entorno: {', '.join(missing_vars)}")

def contar_caracteres(mensaje):
    print("\n=== Conteo de Caracteres ===")
    print(f"Caracteres totales: {len(mensaje)}")
    print(f"Caracteres sin espacios: {len(mensaje.replace(' ', ''))}")
    print(f"Caracteres especiales: {sum(1 for c in mensaje if ord(c) > 127)}")
    print(f"Saltos de línea: {mensaje.count(chr(10))}")
    print("===========================")
    return len(mensaje)

def generar_mensaje():
    prompt = """
Quiero que generes un mensaje diario para enviar por WhatsApp. El mensaje DEBE tener menos de 1150 caracteres en total. El mensaje debe tener tres secciones bien diferenciadas. Sigue exactamente este formato y tono:

FRASES INSPIRADORAS DEL DIA:
Dame 3 frases breves, profundas y motivadoras, extraidas de libros, filosofos, escritores, figuras historicas, emprendedores o lideres de negocios. Cada frase debe estar entre comillas y debe incluir el nombre del autor. Usa frases que sirvan para reflexionar o impulsar el dia.

IDEAS INNOVADORAS DE STARTUPS:
Dame 5 ideas breves de startups con alto potencial. Las ideas deben ser creativas, escalables y resolver problemas reales. Pueden basarse en tecnologia, inteligencia artificial, sostenibilidad, salud mental, educacion, productividad, etc. Que suenen atractivas y posibles de ejecutar.

OPORTUNIDADES DE INVERSION EN ARGENTINA:
Dame 2 ideas de inversion actuales y relevantes para Argentina en este momento (considerando un horizonte temporal de mediano plazo). Para cada idea, incluye:
- Un titulo conciso que describa la inversion
- Una breve descripcion de la oportunidad y los factores a considerar
- Una fuente de informacion confiable donde se pueda profundizar sobre el tema

No incluyas introducciones ni cierres, solo el contenido. El objetivo es que el mensaje sea informativo, inspirador y atractivo para leer en WhatsApp, cada mañana.

IMPORTANTE: 
- El mensaje total NO debe exceder 1150 caracteres bajo ninguna circunstancia.
- Esta PROHIBIDO usar emojis en la respuesta.
- NO uses caracteres especiales (tildes, ñ, etc).
- NO uses corchetes [] ni parentesis () en las URLs.
- Usa solo URLs cortas y simples.
- Minimiza el uso de saltos de linea.
"""
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_NAME,
            },
            data=json.dumps({
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.8
            })
        )
        
        response_data = response.json()
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            content = response_data['choices'][0]['message']['content']
            # Separar las tres secciones
            secciones = {
                'frases': '',
                'ideas': '',
                'oportunidades': ''
            }
            lines = content.split('\n')
            current = None
            for line in lines:
                if line.strip().startswith('FRASES INSPIRADORAS DEL DIA:'):
                    current = 'frases'
                    continue
                elif line.strip().startswith('IDEAS INNOVADORAS DE STARTUPS:'):
                    current = 'ideas'
                    continue
                elif line.strip().startswith('OPORTUNIDADES DE INVERSION EN ARGENTINA:'):
                    current = 'oportunidades'
                    continue
                if current and line.strip():
                    secciones[current] += (line + '\n')
            # Quitar salto de línea final
            for k in secciones:
                secciones[k] = secciones[k].strip()
            return secciones
        else:
            print("Error: Unexpected response format from OpenRouter")
            return None
            
    except Exception as e:
        print(f"Error al hacer la petición a OpenRouter: {str(e)}")
        return None

def enviar_por_whatsapp(secciones):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        from_whatsapp = 'whatsapp:+15557444408'  
        
        if not TWILIO_TEMPLATE_SID:
            raise ValueError("TWILIO_TEMPLATE_SID no está configurado en las variables de entorno")
            
        print(f"Enviando mensaje usando template SID: {TWILIO_TEMPLATE_SID}")
        
        message = client.messages.create(
            from_=from_whatsapp,
            to=TO_WHATSAPP,
            content_sid=TWILIO_TEMPLATE_SID,
            content_variables=json.dumps({
                "1": secciones['frases'],
                "2": secciones['ideas'],
                "3": secciones['oportunidades']
            })
        )
        print("Mensaje enviado exitosamente!")
        return True
    except Exception as e:
        print(f"Error al enviar mensaje por WhatsApp: {str(e)}")
        print(f"Detalles del error: {type(e).__name__}")
        return False

if __name__ == "__main__":
    secciones = generar_mensaje()
    if secciones:
        print("\nMensaje generado correctamente, contando caracteres...")
        total = sum(len(v) for v in secciones.values())
        print(f"Caracteres totales: {total}")
        if total <= 1150:
            print(f"\nIntentando enviar por WhatsApp ({total} caracteres)...")
            enviar_por_whatsapp(secciones)
        else:
            print(f"\nERROR: El mensaje excede el límite de 1150 caracteres ({total} caracteres)")
    else:
        print("No se pudo generar el mensaje, no se enviará por WhatsApp.")
