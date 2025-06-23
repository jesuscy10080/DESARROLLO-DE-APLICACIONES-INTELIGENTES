// Piano Virtual Invisible - Manejo de cámara con pantalla completa CAMERA.JS

// Estado de la cámara
const cameraState = {
    stream: null,
    isRunning: false,
    frameCount: 0,
    lastFrameTime: 0,
    targetFPS: 15  // Frames por segundo objetivo
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log("Camera.js cargado");
    if (typeof debugLog === 'function') {
        debugLog("Camera.js inicializado con soporte de pantalla completa");
    }
    
    // Configurar botones
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const toggleBtn = document.getElementById('toggle-view-btn');
    const prevBtn = document.getElementById('prev-octave');
    const nextBtn = document.getElementById('next-octave');
    
    if (startBtn) startBtn.addEventListener('click', startCamera);
    if (stopBtn) stopBtn.addEventListener('click', stopCamera);
    if (toggleBtn) toggleBtn.addEventListener('click', toggleView);
    if (prevBtn) prevBtn.addEventListener('click', handlePrevOctave);
    if (nextBtn) nextBtn.addEventListener('click', handleNextOctave);
    
    // Verificar que todos los botones existen
    if (typeof debugLog === 'function') {
        debugLog(`Botones encontrados: start=${!!startBtn}, stop=${!!stopBtn}, toggle=${!!toggleBtn}, prev=${!!prevBtn}, next=${!!nextBtn}`);
    }
    
    // Event listeners para cambios de pantalla completa
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
});

// Manejar cambios de pantalla completa
function handleFullscreenChange() {
    const canvas = document.getElementById('canvas');
    const video = document.getElementById('video');
    
    if (canvas && video && cameraState.isRunning) {
        // Pequeño retraso para que las dimensiones se actualicen
        setTimeout(() => {
            // Actualizar dimensiones del canvas
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            if (typeof debugLog === 'function') {
                const isFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement);
                debugLog(`Pantalla completa ${isFullscreen ? 'activada' : 'desactivada'}: Canvas ${canvas.width}x${canvas.height}`);
            }
            
            // Re-renderizar el teclado con las nuevas dimensiones
            if (typeof renderKeyboard === 'function') {
                const ctx = canvas.getContext('2d');
                const testData = {
                    hand_detected: false,
                    is_playing: false,
                    note: null,
                    position: null,
                    navigation: null
                };
                renderKeyboard(ctx, canvas.width, canvas.height, testData);
            }
        }, 100);
    }
}

// Manejar navegación de octava anterior
function handlePrevOctave() {
    if (typeof debugLog === 'function') {
        debugLog("Botón octava anterior presionado");
    }
    
    if (typeof prevOctave === 'function') {
        prevOctave();
    } else if (pianoConfig && (pianoConfig.current_octave_offset || pianoConfig.currentOctaveOffset) > 0) {
        if (pianoConfig.current_octave_offset !== undefined) {
            pianoConfig.current_octave_offset--;
        } else {
            pianoConfig.currentOctaveOffset--;
        }
        if (typeof updateOctaveDisplay === 'function') {
            updateOctaveDisplay();
        }
    }
}

// Manejar navegación de octava siguiente
function handleNextOctave() {
    if (typeof debugLog === 'function') {
        debugLog("Botón octava siguiente presionado");
    }
    
    if (typeof nextOctave === 'function') {
        nextOctave();
    } else if (pianoConfig) {
        const totalOctaves = pianoConfig.total_octaves || pianoConfig.totalOctaves || 5;
        const visibleOctaves = pianoConfig.visible_octaves || pianoConfig.visibleOctaves || 3;
        const currentOffset = pianoConfig.current_octave_offset || pianoConfig.currentOctaveOffset || 0;
        const maxOffset = totalOctaves - visibleOctaves;
        
        if (currentOffset < maxOffset) {
            if (pianoConfig.current_octave_offset !== undefined) {
                pianoConfig.current_octave_offset++;
            } else {
                pianoConfig.currentOctaveOffset++;
            }
            if (typeof updateOctaveDisplay === 'function') {
                updateOctaveDisplay();
            }
        }
    }
}

// Iniciar cámara
async function startCamera() {
    try {
        if (typeof debugLog === 'function') {
            debugLog("Iniciando cámara...");
        }
        
        // Solicitar acceso a cámara con configuración optimizada
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280, min: 640 },
                height: { ideal: 720, min: 480 },
                facingMode: 'user',
                frameRate: { ideal: 30, min: 15 }
            }
        });
        
        if (typeof debugLog === 'function') {
            debugLog("✅ Acceso a cámara obtenido");
        }
        
        // Guardar stream
        cameraState.stream = stream;
        cameraState.isRunning = true;
        
        // Conectar video
        const videoElement = document.getElementById('video');
        videoElement.srcObject = stream;
        
        // Esperar a que el video esté listo
        try {
            await videoElement.play();
            if (typeof debugLog === 'function') {
                debugLog(`✅ Video iniciado: ${videoElement.videoWidth}x${videoElement.videoHeight}`);
            }
        } catch (err) {
            if (typeof debugLog === 'function') {
                debugLog(`❌ Error al reproducir video: ${err.message}`);
            }
            throw err;
        }
        
        // Inicializar canvas con dimensiones correctas
        const canvasElement = document.getElementById('canvas');
        if (canvasElement) {
            canvasElement.width = videoElement.videoWidth;
            canvasElement.height = videoElement.videoHeight;
            
            // Hacer que el canvas sea transparente
            const ctx = canvasElement.getContext('2d');
            ctx.clearRect(0, 0, canvasElement.width, canvasElement.height);
            
            if (typeof debugLog === 'function') {
                debugLog(`✅ Canvas configurado: ${canvasElement.width}x${canvasElement.height}`);
            }
            
            // Renderizar teclado inicial
            if (typeof renderKeyboard === 'function') {
                const testData = {
                    hand_detected: false,
                    is_playing: false,
                    note: null,
                    position: null,
                    navigation: null
                };
                renderKeyboard(ctx, canvasElement.width, canvasElement.height, testData);
                debugLog("✅ Teclado inicial renderizado");
            }
        }
        
        // Actualizar UI
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const toggleBtn = document.getElementById('toggle-view-btn');
        const prevBtn = document.getElementById('prev-octave');
        const nextBtn = document.getElementById('next-octave');
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
        if (toggleBtn) toggleBtn.disabled = false;
        if (prevBtn) prevBtn.disabled = false;
        if (nextBtn) nextBtn.disabled = false;
        if (fullscreenBtn) fullscreenBtn.disabled = false;
        
        // Actualizar estado
        updateStatus('Cámara iniciada - Muestra tu mano para comenzar');
        
        // Actualizar display de octavas
        if (typeof updateOctaveDisplay === 'function') {
            updateOctaveDisplay();
        }
        
        // Iniciar procesamiento con WebSockets
        if (typeof startFrameProcessing === 'function') {
            startFrameProcessing();
            if (typeof debugLog === 'function') {
                debugLog("✅ Iniciando procesamiento de frames con navegación por gestos");
            }
        } else {
            if (typeof debugLog === 'function') {
                debugLog("❌ Error: función startFrameProcessing no encontrada. Verifica que socket.js esté cargado.");
            }
            console.error("Función startFrameProcessing no encontrada. Asegúrate de cargar socket.js antes de camera.js");
        }
    } catch (error) {
        if (typeof debugLog === 'function') {
            debugLog(`❌ Error al iniciar la cámara: ${error.message}`);
        }
        console.error('Error al iniciar la cámara:', error);
        updateStatus('Error: ' + error.message);
    }
}

// Detener cámara
function stopCamera() {
    if (cameraState.stream) {
        if (typeof debugLog === 'function') {
            debugLog("Deteniendo cámara...");
        }
        
        // Detener tracks
        cameraState.stream.getTracks().forEach(track => track.stop());
        cameraState.stream = null;
        cameraState.isRunning = false;
        
        // Limpiar video
        const videoElement = document.getElementById('video');
        videoElement.srcObject = null;
        
        // Limpiar canvas
        const canvasElement = document.getElementById('canvas');
        if (canvasElement) {
            const ctx = canvasElement.getContext('2d');
            ctx.clearRect(0, 0, canvasElement.width, canvasElement.height);
        }
        
        // Ocultar indicadores de navegación
        if (typeof showGestureNavigation === 'function') {
            showGestureNavigation(false);
        }
        
        // Actualizar UI
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const toggleBtn = document.getElementById('toggle-view-btn');
        const prevBtn = document.getElementById('prev-octave');
        const nextBtn = document.getElementById('next-octave');
        const noteDisplay = document.getElementById('note-display');
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        if (toggleBtn) toggleBtn.disabled = true;
        if (prevBtn) prevBtn.disabled = true;
        if (nextBtn) nextBtn.disabled = true;
        if (noteDisplay) noteDisplay.textContent = '-';
        if (fullscreenBtn) fullscreenBtn.disabled = true;
        
        // Salir de pantalla completa si está activa
        if (document.fullscreenElement) {
            document.exitFullscreen();
        }
        
        // Actualizar estado
        updateStatus('Cámara detenida');
        if (typeof debugLog === 'function') {
            debugLog("✅ Cámara detenida");
        }
    }
}

// Alternar vista del teclado
function toggleView() {
    const canvasElement = document.getElementById('canvas');
    const toggleBtn = document.getElementById('toggle-view-btn');
    
    if (canvasElement && toggleBtn) {
        if (canvasElement.style.display === 'none') {
            canvasElement.style.display = 'block';
            toggleBtn.textContent = 'Ocultar Teclado';
            if (typeof debugLog === 'function') {
                debugLog("Teclado visible");
            }
            
            // Re-renderizar si hay datos
            if (typeof renderKeyboard === 'function' && cameraState.isRunning) {
                const ctx = canvasElement.getContext('2d');
                const testData = {
                    hand_detected: false,
                    is_playing: false,
                    note: null,
                    position: null,
                    navigation: null
                };
                renderKeyboard(ctx, canvasElement.width, canvasElement.height, testData);
            }
        } else {
            canvasElement.style.display = 'none';
            toggleBtn.textContent = 'Mostrar Teclado';
            if (typeof debugLog === 'function') {
                debugLog("Teclado oculto");
            }
        }
    }
}

// Actualizar mensaje de estado
function updateStatus(message) {
    const statusElement = document.getElementById('status');
    if (statusElement) {
        statusElement.textContent = message;
    }
}

// Hacer funciones disponibles globalmente
window.handlePrevOctave = handlePrevOctave;
window.handleNextOctave = handleNextOctave;
window.handleFullscreenChange = handleFullscreenChange;

// Mensaje de depuración
console.log("📷 Camera.js cargado correctamente con soporte de pantalla completa");