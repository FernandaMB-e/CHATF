// Referencias a elementos del DOM
const inputPregunta = document.getElementById('input-pregunta');
const btnEnviar = document.getElementById('btn-enviar');
const chatHistorial = document.getElementById('chat-historial');
const estadoTexto = document.getElementById('estado-texto');
const bocaSvg = document.getElementById('boca');
const cejaIzq = document.getElementById('ceja-izq');
const cejaDer = document.getElementById('ceja-der');
const ojoIzq = document.getElementById('ojo-izq');
const ojoDer = document.getElementById('ojo-der');
const brilloIzq = document.getElementById('brillo-izq');
const brilloDer = document.getElementById('brillo-der');
const ruborIzq = document.getElementById('rubor-izq');
const ruborDer = document.getElementById('rubor-der');
const efectosAnimar = document.getElementById('efectos-animar');
const btnMic = document.getElementById('btn-mic')

// Conexión WebSocket con el servidor Python (FastAPI)
const ws = new WebSocket("ws://127.0.0.1:8000/ws");
// Configuración nativa de Web Speech API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;


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


if (SpeechRecognition) {
    const reconocimiento = new SpeechRecognition();
    reconocimiento.lang = 'es-MX'; // Configurado para acento y vocabulario local
    reconocimiento.continuous = false;
    reconocimiento.interimResults = false;

    // Al hacer clic en el micrófono
    btnMic.addEventListener('click', () => {
        reconocimiento.start();
        btnMic.classList.add('grabando');
        inputPregunta.placeholder = "Escuchando...";
    });

    // Cuando detecta lo que dijiste
    reconocimiento.onresult = (evento) => {
        const transcripcion = evento.results[0][0].transcript;
        inputPregunta.value = transcripcion; // Pone el texto en la barra
        
        btnMic.classList.remove('grabando');
        inputPregunta.placeholder = "Escribe o dicta tu pregunta...";
        
        // Opcional: Descomenta la siguiente línea si quieres que se envíe sola al terminar de hablar
        // btnEnviar.click(); 
    };

    // Si ocurre un error o hay silencio absoluto
    reconocimiento.onerror = (evento) => {
        console.error("Error de reconocimiento: ", evento.error);
        btnMic.classList.remove('grabando');
        inputPregunta.placeholder = "Escribe o dicta tu pregunta...";
    };

    reconocimiento.onspeechend = () => {
        reconocimiento.stop();
    };

} else {
    console.warn("Tu navegador actual no soporta dictado por voz.");
    btnMic.style.display = "none"; // Oculta el botón si el navegador no es compatible (ej. Firefox antiguo)
}

// Control dinámico de las expresiones del SVG
function cambiarExpresion(emocion) {
    document.body.classList.remove('estado-incoherente', 'estado-correccion');
    // 1. Valores Neutrales por defecto
    let dBoca = 'M 85 125 Q 100 135 115 125';
    let dCejaIzq = 'M 55 75 Q 65 70 75 75';
    let dCejaDer = 'M 125 75 Q 135 70 145 75';
    let ryOjo = '14'; // Altura del ojo abierto
    let opBrillo = '1';
    let colorRubor = '#ffb6c1';
    let radioRubor = '14';
    let opEfectos = '0';

    // 2. Comportamientos empáticos para cada emoción
    if (emocion === 'frustracion' || emocion === 'enojo') {
        document.body.classList.add('estado-correccion');
        // Disculpa empática: Ojos cerrados (ry=2), rubor intenso y grande, sonrisa apenada, cejas compasivas
        dBoca = 'M 80 128 Q 100 135 120 128'; 
        dCejaIzq = 'M 55 75 Q 65 60 75 80'; 
        dCejaDer = 'M 125 80 Q 135 60 145 75';
        colorRubor = '#ff4757'; 
        radioRubor = '18';

    } else if (emocion === 'incoherente') {
        // La IA está dando la mala respuesta intencionalmente: Ojos temblando y Fondo Frío
        document.body.classList.add('estado-incoherente');
        
        dBoca = 'M 85 125 Q 100 120 115 125'; // Boca recta/tensa
        dCejaIzq = 'M 55 75 Q 65 85 75 75'; // Cejas ligeramente hacia abajo
        dCejaDer = 'M 125 75 Q 135 85 145 75';
        opBrillo = '1';
        
        
    } else if (emocion === 'tristeza') {
        // Intentar animar: Boca cantando, notas musicales y corazones
        dBoca = 'M 90 125 Q 100 145 110 125'; // Boquita cantando/hablando tierno
        dCejaIzq = 'M 55 70 Q 65 60 75 75'; 
        dCejaDer = 'M 125 75 Q 135 60 145 70';
        opEfectos = '1'; // Muestra la música y corazones
        
    } else if (emocion === 'sorpresa' || emocion === 'miedo') {
        // Susto/Sorpresa: Ojos y boca gigante, cejas volando
        dBoca = 'M 85 125 Q 100 155 115 125'; 
        dCejaIzq = 'M 55 60 Q 65 50 75 60'; 
        dCejaDer = 'M 125 60 Q 135 50 145 60';
        ryOjo = '17'; // Ojos súper abiertos
        
    } else if (emocion === 'felicidad') {
        dBoca = 'M 70 120 Q 100 150 130 120'; // Sonrisa enorme
        dCejaIzq = 'M 55 70 Q 65 60 75 70';
        dCejaDer = 'M 125 70 Q 135 60 145 70';
        
    } else if (emocion === 'pensando') {
        dBoca = 'M 85 125 Q 100 125 115 120'; 
        dCejaIzq = 'M 55 75 Q 65 70 75 75'; 
        dCejaDer = 'M 125 65 Q 135 60 145 65'; 
        
    } else if (emocion === 'hablando') {
        dBoca = 'M 85 118 Q 100 140 115 118';
    }

    // 3. Aplicamos todo al dibujo SVG
    if(bocaSvg) bocaSvg.setAttribute('d', dBoca);
    if(cejaIzq) cejaIzq.setAttribute('d', dCejaIzq);
    if(cejaDer) cejaDer.setAttribute('d', dCejaDer);
    if(ojoIzq) ojoIzq.setAttribute('ry', ryOjo);
    if(ojoDer) ojoDer.setAttribute('ry', ryOjo);
    if(brilloIzq) brilloIzq.style.opacity = opBrillo;
    if(brilloDer) brilloDer.style.opacity = opBrillo;
    if(ruborIzq) {
        ruborIzq.setAttribute('fill', colorRubor);
        ruborIzq.setAttribute('r', radioRubor);
    }
    if(ruborDer) {
        ruborDer.setAttribute('fill', colorRubor);
        ruborDer.setAttribute('r', radioRubor);
    }
    if(efectosAnimar) efectosAnimar.style.opacity = opEfectos;
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


