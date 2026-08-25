// Referencias a elementos del DOM
const inputPregunta = document.getElementById('input-pregunta');
const btnEnviar = document.getElementById('btn-enviar');
const chatHistorial = document.getElementById('chat-historial');
const estadoTexto = document.getElementById('estado-texto');
const bocaSvg = document.getElementById('boca');

// Conexión WebSocket con el servidor Python (FastAPI)
const ws = new WebSocket("ws://127.0.0.1:8000/ws");

ws.onopen = () => {
    console.log("[CONEXIÓN] Conectado al servidor de Inteligencia Artificial afectiva.");
    estadoTexto.textContent = "Esperando tu pregunta...";
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Actualizar texto de estado inferior
    if (data.texto && data.estado) {
        estadoTexto.textContent = data.texto;
    }

    // Cambiar expresiones de la carita según la orden de Python
    cambiarExpresion(data.estado);

    // Si viene texto para agregar al historial del chat
    if (data.tipo && data.texto) {
        agregarMensaje(data.texto, 'ia');
    }
};

ws.onclose = () => {
    console.warn("[CONEXIÓN] Se perdió la conexión con el servidor Python.");
    estadoTexto.textContent = "Desconectado del servidor.";
};

// Función para agregar mensajes al chat
function agregarMensaje(texto, tipo) {
    const divMensaje = document.createElement('div');
    divMensaje.classList.add('mensaje');
    
    if (tipo === 'usuario') {
        divMensaje.classList.add('mensaje-usuario');
    } else {
        divMensaje.classList.add('mensaje-ia');
    }
    
    divMensaje.textContent = texto;
    chatHistorial.appendChild(divMensaje);
    chatHistorial.scrollTop = chatHistorial.scrollHeight;
}

// Control dinámico de las expresiones del SVG
function cambiarExpresion(tipo) {
    if (tipo === 'feliz') {
        bocaSvg.setAttribute('d', 'M 75 120 Q 100 145 125 120'); // Sonrisa amplia
    } else if (tipo === 'hablando') {
        bocaSvg.setAttribute('d', 'M 85 118 Q 100 140 115 118'); // Boca abierta hablando
    } else if (tipo === 'pensando') {
        bocaSvg.setAttribute('d', 'M 85 125 Q 100 125 115 125'); // Línea recta neutra
    } else {
        bocaSvg.setAttribute('d', 'M 85 125 Q 100 135 115 125'); // Normal
    }
}

// Enviar pregunta al servidor Python por WebSocket
function manejarEnvio() {
    const texto = inputPregunta.value.trim();
    if (!texto) return;

    // Mostrar pregunta del usuario en pantalla
    agregarMensaje(texto, 'usuario');
    inputPregunta.value = '';

    // Enviar a Python a través del WebSocket
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(texto);
    } else {
        alert("El servidor no está activo. Asegúrate de ejecutar server.py");
    }
}

// Eventos de interacción
btnEnviar.addEventListener('click', manejarEnvio);
inputPregunta.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        manejarEnvio();
    }
});