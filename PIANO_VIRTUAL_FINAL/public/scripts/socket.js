// Socket.js - Versión simplificada como tu código original
const socket = io();

// Variables globales
let frameProcessingActive = false;
let lastFrameTime = 0;
const targetFPS = 15;

// Conexión socket
socket.on('connect', function() {
    console.log('🔗 Conectado al servidor');
    updateStatus('Conectado');
});

socket.on('disconnect', function() {
    console.log('❌ Desconectado del servidor');
    updateStatus('Desconectado');
});

// Procesar respuesta del servidor
socket.on('frame_processed', function(data) {
    try {
        // Mostrar imagen procesada con landmarks y teclado
        const processedVideo = document.getElementById('processedVideo');
        if (processedVideo && data.image) {
            processedVideo.src = data.image;
        }
        
        // Actualizar información de manos
        updateHandsInfo(data.hands || []);
        
        // Actualizar teclas presionadas
        updatePressedKeys(data.pressed_keys || []);
        
        // Actualizar octava
        if (data.octava_actual) {
            updateOctaveDisplay(data.octava_actual);
        }
        
        // Stats
        updateStats(data.frame_count || 0);
        
    } catch (error) {
        console.error('Error procesando respuesta:', error);
    }
});

socket.on('error', function(data) {
    console.error('Error del servidor:', data.message);
    updateStatus('Error: ' + data.message);
});

// Función para enviar frame al servidor
function sendFrameToServer(canvas) {
    if (!frameProcessingActive) return;
    
    // Control de FPS
    const now = Date.now();
    if (now - lastFrameTime < 1000 / targetFPS) {
        return;
    }
    lastFrameTime = now;
    
    try {
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        socket.emit('process_frame', {
            image: imageData,
            timestamp: now
        });
    } catch (error) {
        console.error('Error enviando frame:', error);
    }
}

// Actualizar información de manos
function updateHandsInfo(hands) {
    const handsInfo = document.getElementById('handsInfo');
    if (!handsInfo) return;
    
    if (hands.length === 0) {
        handsInfo.innerHTML = '<p>No se detectan manos</p>';
        return;
    }
    
    let html = '<h3>Manos Detectadas:</h3>';
    hands.forEach((hand, index) => {
        html += `
            <div class="hand-info">
                <h4>Mano ${hand.hand_label}</h4>
                <div class="landmarks-grid">
        `;
        
        // Mostrar solo landmarks importantes
        const importantLandmarks = [0, 4, 8, 12, 16, 20]; // Muñeca y puntas de dedos
        const landmarkNames = ['Muñeca', 'Pulgar', 'Índice', 'Medio', 'Anular', 'Meñique'];
        
        importantLandmarks.forEach((idx, i) => {
            const landmark = hand.landmarks[idx];
            if (landmark) {
                html += `
                    <div class="landmark">
                        <strong>${landmarkNames[i]}:</strong>
                        (${landmark.x.toFixed(3)}, ${landmark.y.toFixed(3)})
                    </div>
                `;
            }
        });
        
        html += '</div></div>';
    });
    
    handsInfo.innerHTML = html;
}

// Actualizar teclas presionadas
function updatePressedKeys(pressedKeys) {
    const pressedKeysInfo = document.getElementById('pressedKeysInfo');
    if (!pressedKeysInfo) return;
    
    if (pressedKeys.length === 0) {
        pressedKeysInfo.innerHTML = '<p>Ninguna tecla presionada</p>';
        return;
    }
    
    let html = '<h3>Teclas Presionadas:</h3>';
    pressedKeys.forEach(key => {
        html += `
            <div class="pressed-key">
                🎵 ${key.finger}: <strong>${key.nota}${key.octava}</strong>
            </div>
        `;
    });
    
    pressedKeysInfo.innerHTML = html;
}

// Actualizar display de octava
function updateOctaveDisplay(octava) {
    const octaveDisplay = document.getElementById('currentOctave');
    if (octaveDisplay) {
        octaveDisplay.textContent = octava;
    }
}

// Actualizar estadísticas
function updateStats(frameCount) {
    const statsElement = document.getElementById('stats');
    if (statsElement) {
        const fps = frameCount > 0 ? (frameCount % 100) : 0;
        statsElement.innerHTML = `
            <p>Frames procesados: ${frameCount}</p>
            <p>FPS objetivo: ${targetFPS}</p>
        `;
    }
}

// Actualizar status
function updateStatus(status) {
    const statusElement = document.getElementById('status');
    if (statusElement) {
        statusElement.textContent = status;
    }
}

// Funciones para cambiar octava
function changeOctave(direction) {
    fetch('/api/change_octave', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ direction: direction })
    })
    .then(response => response.json())
    .then(data => {
        updateOctaveDisplay(data.octava_actual);
        console.log(`Octava cambiada a: ${data.octava_actual}`);
    })
    .catch(error => {
        console.error('Error cambiando octava:', error);
    });
}

// Inicializar cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎹 Socket.js inicializado');
    
    // Configurar botones de octava
    const prevOctaveBtn = document.getElementById('prevOctave');
    const nextOctaveBtn = document.getElementById('nextOctave');
    
    if (prevOctaveBtn) {
        prevOctaveBtn.addEventListener('click', () => changeOctave('prev'));
    }
    
    if (nextOctaveBtn) {
        nextOctaveBtn.addEventListener('click', () => changeOctave('next'));
    }
});

// Exportar funciones para uso en camera.js
window.sendFrameToServer = sendFrameToServer;
window.setFrameProcessing = function(active) {
    frameProcessingActive = active;
    console.log('Frame processing:', active ? 'ACTIVADO' : 'DESACTIVADO');
};