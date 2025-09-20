from flask import Flask, render_template, request, jsonify
from chatbot_engine import MotorRespuestasAvanzado
import logging
import os

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Inicializar el motor de chatbot
motor = MotorRespuestasAvanzado()

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'response': 'Por favor, escribe un mensaje.'})
        
        # Procesar el mensaje con el motor
        response = motor.procesar_mensaje(user_message)
        
        return jsonify({'response': response})
        
    except Exception as e:
        logger.error(f"Error en endpoint /chat: {str(e)}")
        return jsonify({'response': 'Lo siento, ocurrió un error procesando tu mensaje.'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)