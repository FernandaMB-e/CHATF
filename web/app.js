// Referencias a elementos del DOM
const inputPregunta = document.getElementById('input-pregunta');
const btnEnviar = document.getElementById('btn-enviar');
const chatHistorial = document.getElementById('chat-historial');
const estadoTexto = document.getElementById('estado-texto');
const bocaSvg = document.getElementById('boca');
const cejaIzq = document.getElementById('ceja-izq');
const cejaDer = document.getElementById('ceja-der');
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
// Control dinámico de expresiones faciales (Boca y Cejas)
function cambiarExpresion(estado) {
    // 1. Configuraciones por defecto (Estado Neutral)
    let dBoca = 'M 85 125 Q 100 135 115 125';
    let dCejaIzq = 'M 55 75 Q 65 70 75 75';
    let dCejaDer = 'M 125 75 Q 135 70 145 75';

    if (estado === 'feliz' || estado === 'hablando-feliz') {
        // Sonrisa grande y cejas arqueadas de felicidad
        dBoca = (estado === 'feliz') ? 'M 70 120 Q 100 150 130 120' : 'M 80 115 Q 100 145 120 115';
        dCejaIzq = 'M 55 70 Q 65 60 75 70';
        dCejaDer = 'M 125 70 Q 135 60 145 70';
        
    } else if (estado === 'empatico' || estado === 'hablando-empatico') {
        // Cejas curvas hacia adentro (tristeza/empatía) y boca suave
        dBoca = (estado === 'empatico') ? 'M 80 128 Q 100 120 120 128' : 'M 85 122 Q 100 135 115 122'; 
        dCejaIzq = 'M 55 75 Q 65 60 75 80'; 
        dCejaDer = 'M 125 80 Q 135 60 145 75';
        
    } else if (estado === 'sorpresa') {
        // Boca en "O" y cejas altísimas
        dBoca = 'M 85 125 Q 100 150 115 125'; 
        dCejaIzq = 'M 55 65 Q 65 50 75 65'; 
        dCejaDer = 'M 125 65 Q 135 50 145 65';
        
    } else if (estado === 'pensando') {
        // Boca ladeada y una ceja levantada (estilo dudoso)
        dBoca = 'M 85 125 Q 100 125 115 120'; 
        dCejaIzq = 'M 55 75 Q 65 70 75 75'; 
        dCejaDer = 'M 125 65 Q 135 60 145 65'; 
        
    } else if (estado === 'hablando') {
        // Hablando neutral
        dBoca = 'M 85 118 Q 100 140 115 118';
    }

    // 2. Aplicar las transformaciones al SVG
    bocaSvg.setAttribute('d', dBoca);
    if(cejaIzq && cejaDer) {
        // Añadimos una transición suave vía CSS/JS directo
        cejaIzq.style.transition = "d 0.3s ease";
        cejaDer.style.transition = "d 0.3s ease";
        bocaSvg.style.transition = "d 0.3s ease";
        
        cejaIzq.setAttribute('d', dCejaIzq);
        cejaDer.setAttribute('d', dCejaDer);
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