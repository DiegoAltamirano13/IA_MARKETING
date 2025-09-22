from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from chatbot_engine import MotorRespuestasAvanzado
from dotenv import load_dotenv
load_dotenv()  # Añade esto al inicio del archivo
import logging
import os

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Inicializar motor y cliente de Twilio
motor = MotorRespuestasAvanzado()

# Configuración de Twilio (usa variables de entorno por seguridad)
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_client = Client(twilio_account_sid, twilio_auth_token) if twilio_account_sid and twilio_auth_token else None

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat_web():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'response': 'Por favor, escribe un mensaje.'})
        
        response = motor.procesar_mensaje(user_message)
        return jsonify({'response': response})
        
    except Exception as e:
        logger.error(f"Error en /chat: {str(e)}")
        return jsonify({'response': 'Error procesando tu mensaje.'})

@app.route('/whatsapp', methods=['POST'])
def chat_whatsapp():
    try:
        # Verificar que es una solicitud válida de Twilio (opcional pero recomendado)
        if not es_solicitud_valida_twilio(request):
            return "Unauthorized", 403
        
        user_message = request.form.get('Body', '').strip()
        from_number = request.form.get('From', '')
        
        logger.info(f"WhatsApp de {from_number}: {user_message}")
        
        if not user_message:
            return "Mensaje vacío", 400
        
        # Procesar mensaje
        response = motor.procesar_mensaje(user_message)
        
        # Crear respuesta Twilio
        twilio_response = MessagingResponse()
        twilio_response.message(response)
        
        return str(twilio_response)
        
    except Exception as e:
        logger.error(f"Error en /whatsapp: {str(e)}")
        twilio_response = MessagingResponse()
        twilio_response.message("❌ Error procesando tu mensaje.")
        return str(twilio_response)

def es_solicitud_valida_twilio(request):
    """Verifica que la solicitud viene de Twilio (opcional pero recomendado)"""
    # Puedes implementar verificación de firma Twilio aquí
    # https://www.twilio.com/docs/usage/webhooks/webhooks-security
    return True  # Por ahora retornamos True para testing

@app.route('/test-twilio', methods=['GET'])
def test_twilio():
    """Endpoint para probar la conexión con Twilio"""
    if not twilio_client:
        return jsonify({'status': 'error', 'message': 'Twilio no configurado'})
    
    try:
        # Intentar obtener información de la cuenta
        account = twilio_client.api.accounts(twilio_account_sid).fetch()
        return jsonify({
            'status': 'success', 
            'message': 'Twilio conectado correctamente',
            'account': account.friendly_name
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)