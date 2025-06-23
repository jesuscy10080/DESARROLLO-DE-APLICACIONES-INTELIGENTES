// Piano Virtual Invisible - Lógica del piano MULTI-FINGER

// Estado del piano
const pianoState = {
    lastNotes: [],
    lastPlayedTime: 0,
    noteDebounceTime: 100,  // Menor tiempo para multi-dedo
    activeNotes: new Set()  // Para rastrear notas activas
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log("Piano.js Multi-Finger cargado");
    if (typeof debugLog === 'function') {
        debugLog("Piano.js Multi-Finger inicializado");
        debugLog(`Configuración inicial: ${JSON.stringify(pianoConfig)}`);
    }
});

// Mostrar múltiples notas activas
function displayActiveNotes(activeNotes) {
    const noteDisplay = document.getElementById('note-display');
    if (noteDisplay) {
        if (activeNotes && activeNotes.length > 0) {
            const noteNames = activeNotes.map(n => n.note).join(' + ');
            noteDisplay.textContent = noteNames;
            noteDisplay.classList.add('active');
            
            setTimeout(() => {
                noteDisplay.classList.remove('active');
            }, 500);
        } else {
            noteDisplay.textContent = '-';
        }
    }
}

// ✅ FUNCIÓN PRINCIPAL: RENDERIZAR TECLADO MULTI-FINGER
function renderKeyboard(ctx, width, height, data) {
    try {
        // Limpiar canvas
        ctx.clearRect(0, 0, width, height);
        
        if (!width || !height || width <= 0 || height <= 0) {
            console.log("Dimensiones inválidas para renderizar:", width, height);
            return;
        }
        
        if (!pianoConfig) {
            console.error("pianoConfig no está definido");
            return;
        }
        
        // ✅ CONFIGURACIÓN DEL TECLADO (Zona superior como el código de referencia)
        const keyboardTop = Math.round(height * 0.05);    // 5% desde arriba
        const keyboardHeight = Math.round(height * 0.35); // 35% de altura
        const keyboardBottom = keyboardTop + keyboardHeight;
        
        // ✅ EXTRAER DATOS DEL FRAME
        const handDetected = data && data.hand_detected;
        const activeNotes = data && data.active_notes ? data.active_notes : [];
        const handsCount = data && data.hands_count ? data.hands_count : 0;
        
        // Usar configuración de pianoConfig
        const minOctave = pianoConfig.min_octave || 2;
        const currentOffset = pianoConfig.current_octave_offset || 0;
        const visibleOctaves = pianoConfig.visible_octaves || 3;
        const maxOctave = pianoConfig.max_octave || 6;
        
        // ✅ FONDO DEL TECLADO
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(0, keyboardTop, width, keyboardHeight);
        
        // ✅ BORDE DINÁMICO SEGÚN ESTADO
        let borderColor = '#00FFFF'; // Azul por defecto
        if (activeNotes.length > 0) {
            borderColor = '#00FF00'; // Verde si hay notas activas
        } else if (handDetected) {
            borderColor = '#FFFF00'; // Amarillo si detecta mano
        }
        
        ctx.strokeStyle = borderColor;
        ctx.lineWidth = 4;
        ctx.strokeRect(2, keyboardTop, width - 4, keyboardHeight);
        
        // ✅ CALCULAR DIMENSIONES DE TECLAS
        const notesPerOctave = 12; // DO, DOS, RE, RES, MI, FA, FAS, SOL, SOLS, LA, LAS, SI
        const totalNotes = visibleOctaves * notesPerOctave;
        const noteWidth = (width - 4) / totalNotes;
        
        // ✅ NOTAS Y COLORES
        const notesInOctave = ['DO', 'DOS', 'RE', 'RES', 'MI', 'FA', 'FAS', 'SOL', 'SOLS', 'LA', 'LAS', 'SI'];
        const whiteNotes = ['DO', 'RE', 'MI', 'FA', 'SOL', 'LA', 'SI'];
        const blackNotes = ['DOS', 'RES', 'FAS', 'SOLS', 'LAS'];
        
        const noteColors = {
            'DO': 'rgba(255, 107, 107, 0.9)',   // Rojo
            'RE': 'rgba(255, 142, 83, 0.9)',    // Naranja
            'MI': 'rgba(255, 235, 59, 0.9)',    // Amarillo
            'FA': 'rgba(76, 175, 80, 0.9)',     // Verde
            'SOL': 'rgba(33, 150, 243, 0.9)',   // Azul
            'LA': 'rgba(156, 39, 176, 0.9)',    // Violeta
            'SI': 'rgba(233, 30, 99, 0.9)',     // Rosa
            'DOS': 'rgba(255, 152, 0, 0.9)',    // Naranja oscuro
            'RES': 'rgba(255, 193, 7, 0.9)',    // Amarillo oscuro
            'FAS': 'rgba(139, 195, 74, 0.9)',   // Verde oscuro
            'SOLS': 'rgba(63, 81, 181, 0.9)',   // Azul oscuro
            'LAS': 'rgba(142, 36, 170, 0.9)'    // Violeta oscuro
        };
        
        // ✅ CREAR SET DE NOTAS ACTIVAS PARA COLOREAR
        const activeNotesSet = new Set();
        activeNotes.forEach(noteInfo => {
            activeNotesSet.add(noteInfo.note);
        });
        
        // ✅ DIBUJAR TODAS LAS TECLAS
        for (let octave = 0; octave < visibleOctaves; octave++) {
            const currentOctave = minOctave + currentOffset + octave;
            
            if (currentOctave > maxOctave) break;
            
            // Dibujar cada nota de la octava
            for (let noteIndex = 0; noteIndex < notesPerOctave; noteIndex++) {
                const totalNoteIndex = octave * notesPerOctave + noteIndex;
                const x = 2 + totalNoteIndex * noteWidth;
                const noteName = notesInOctave[noteIndex];
                const fullNote = `${noteName}${currentOctave}`;
                
                // Determinar si es tecla blanca o negra
                const isBlackKey = blackNotes.includes(noteName);
                
                // Dimensiones de la tecla
                const keyWidth = noteWidth - 1;
                const keyHeight = isBlackKey ? keyboardHeight * 0.6 : keyboardHeight - 4;
                const keyY = keyboardTop + 2;
                
                // Color de la tecla
                let keyColor = isBlackKey ? 'rgba(30, 30, 30, 0.8)' : 'rgba(255, 255, 255, 0.4)';
                let textColor = isBlackKey ? 'rgba(255, 255, 255, 1.0)' : 'rgba(0, 0, 0, 1.0)';
                
                // ✅ COLOREAR SI LA NOTA ESTÁ ACTIVA
                if (activeNotesSet.has(fullNote)) {
                    keyColor = noteColors[noteName] || 'rgba(255, 255, 0, 0.8)';
                    textColor = 'rgba(255, 255, 255, 1.0)';
                }
                
                // Dibujar tecla
                ctx.fillStyle = keyColor;
                ctx.fillRect(x, keyY, keyWidth, keyHeight);
                
                // Borde de la tecla
                ctx.strokeStyle = activeNotesSet.has(fullNote) ? 'rgba(255, 255, 255, 1.0)' : 'rgba(100, 100, 100, 0.6)';
                ctx.lineWidth = 1;
                ctx.strokeRect(x, keyY, keyWidth, keyHeight);
                
                // Etiqueta de la nota
                ctx.fillStyle = textColor;
                ctx.font = isBlackKey ? 'bold 10px Arial' : 'bold 12px Arial';
                ctx.textAlign = 'center';
                
                const textX = x + keyWidth / 2;
                const textY = keyY + keyHeight - (isBlackKey ? 8 : 12);
                ctx.fillText(fullNote, textX, textY);
            }
        }
        
        // ✅ DIBUJAR INFORMACIÓN DE ESTADO (Esquina superior izquierda)
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        ctx.fillRect(10, 10, 450, 120);
        
        let statusY = 30;
        
        if (activeNotes.length > 0) {
            // Mostrar notas activas
            ctx.fillStyle = '#00FF00';
            ctx.font = 'bold 18px Arial';
            ctx.textAlign = 'left';
            
            if (activeNotes.length === 1) {
                const note = activeNotes[0];
                ctx.fillText(`♪ Nota: ${note.note}`, 20, statusY);
                ctx.fillText(`👆 Dedo: ${note.finger} (${note.hand})`, 20, statusY + 25);
            } else {
                ctx.fillText(`♪ Acordes: ${activeNotes.length} notas`, 20, statusY);
                const noteNames = activeNotes.map(n => n.note).join(', ');
                ctx.font = 'bold 14px Arial';
                ctx.fillText(`Notas: ${noteNames}`, 20, statusY + 25);
            }
            statusY += 50;
        } else if (handDetected) {
            ctx.fillStyle = '#FFFF00';
            ctx.font = 'bold 16px Arial';
            ctx.textAlign = 'left';
            ctx.fillText(`✋ ${handsCount} mano(s) detectada(s)`, 20, statusY);
            ctx.fillText('Levanta dedos sobre las teclas', 20, statusY + 20);
            statusY += 45;
        } else {
            ctx.fillStyle = '#FFFFFF';
            ctx.font = 'bold 16px Arial';
            ctx.textAlign = 'left';
            ctx.fillText('⏳ Esperando manos...', 20, statusY);
            ctx.fillText('Levanta dedos para tocar', 20, statusY + 20);
            statusY += 45;
        }
        
        // Mostrar octavas actuales
        const startOctave = minOctave + currentOffset;
        const endOctave = Math.min(startOctave + visibleOctaves - 1, maxOctave);
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 14px Arial';
        ctx.fillText(`🎹 Octavas: ${startOctave}-${endOctave}`, 20, statusY);
        
        // ✅ DIBUJAR POSICIONES DE DEDOS ACTIVOS
        if (activeNotes.length > 0) {
            activeNotes.forEach((noteInfo, index) => {
                if (noteInfo.position) {
                    const x = noteInfo.position.x * width;
                    const y = noteInfo.position.y * height;
                    
                    // Círculo del dedo
                    ctx.beginPath();
                    ctx.arc(x, y, 8, 0, Math.PI * 2);
                    ctx.fillStyle = noteColors[noteInfo.note.slice(0, -1)] || '#FF0000';
                    ctx.fill();
                    
                    // Borde blanco
                    ctx.strokeStyle = '#FFFFFF';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                    
                    // Etiqueta del dedo
                    ctx.fillStyle = '#FFFFFF';
                    ctx.font = 'bold 10px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText(noteInfo.finger[0], x, y - 12); // Primera letra del dedo
                }
            });
        }
        
        // ✅ INSTRUCCIONES EN LA PARTE INFERIOR
        if (handDetected) {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('👆 Levanta dedos sobre las teclas para tocar', width / 2, height - 20);
        }
        
    } catch (error) {
        console.error("Error en renderKeyboard Multi-Finger:", error);
        if (typeof debugLog === 'function') {
            debugLog(`Error en renderKeyboard: ${error.message}`);
        }
    }
}

// ✅ FUNCIÓN PARA MANEJAR DATOS DE FRAME MULTI-FINGER
function handleMultiFingerData(data) {
    try {
        // Actualizar display de notas activas
        if (data.active_notes && data.active_notes.length > 0) {
            displayActiveNotes(data.active_notes);
            
            // Log de debug
            if (typeof debugLog === 'function') {
                const noteNames = data.active_notes.map(n => `${n.note}(${n.finger})`).join(', ');
                debugLog(`🎵 Notas activas: ${noteNames}`);
            }
        }
        
        // Actualizar estado del piano
        pianoState.lastNotes = data.active_notes || [];
        pianoState.lastPlayedTime = Date.now();
        
        return true;
    } catch (error) {
        console.error("Error en handleMultiFingerData:", error);
        return false;
    }
}

// Resto de funciones (adaptadas para multi-finger)
function updateOctaveDisplay() {
    if (typeof debugLog === 'function') {
        debugLog(`Actualizando display de octavas`);
    }
    
    const currentOctaveElement = document.getElementById('current-octave');
    if (currentOctaveElement && pianoConfig) {
        const minOctave = pianoConfig.min_octave || 2;
        const currentOffset = pianoConfig.current_octave_offset || 0;
        const visibleOctaves = pianoConfig.visible_octaves || 3;
        const maxOctave = pianoConfig.max_octave || 6;
        const totalOctaves = pianoConfig.total_octaves || 5;
        
        const start = minOctave + currentOffset;
        const end = Math.min(start + visibleOctaves - 1, maxOctave);
        currentOctaveElement.textContent = `Octavas: ${start}-${end} de ${minOctave}-${maxOctave}`;
        
        const prevBtn = document.getElementById('prev-octave');
        const nextBtn = document.getElementById('next-octave');
        
        if (prevBtn) {
            prevBtn.disabled = (currentOffset === 0);
        }
        
        if (nextBtn) {
            nextBtn.disabled = (currentOffset >= totalOctaves - visibleOctaves);
        }
        
        // Re-renderizar teclado
        const canvas = document.getElementById('canvas');
        if (canvas && canvas.width > 0 && canvas.height > 0) {
            const ctx = canvas.getContext('2d');
            const testData = {
                hand_detected: false,
                active_notes: [],
                hands_count: 0
            };
            renderKeyboard(ctx, canvas.width, canvas.height, testData);
        }
        
        if (typeof debugLog === 'function') {
            debugLog(`Display actualizado: ${start}-${end}, offset: ${currentOffset}`);
        }
    }
}

function prevOctave() {
    if (pianoConfig && pianoConfig.current_octave_offset > 0) {
        pianoConfig.current_octave_offset--;
        updateOctaveDisplay();
        if (typeof debugLog === 'function') {
            debugLog(`Octava anterior: nuevo offset = ${pianoConfig.current_octave_offset}`);
        }
    }
}

function nextOctave() {
    if (pianoConfig) {
        const totalOctaves = pianoConfig.total_octaves || 5;
        const visibleOctaves = pianoConfig.visible_octaves || 3;
        const currentOffset = pianoConfig.current_octave_offset || 0;
        const maxOffset = totalOctaves - visibleOctaves;
        
        if (currentOffset < maxOffset) {
            pianoConfig.current_octave_offset++;
            updateOctaveDisplay();
            if (typeof debugLog === 'function') {
                debugLog(`Octava siguiente: nuevo offset = ${pianoConfig.current_octave_offset}`);
            }
        }
    }
}

// Hacer funciones disponibles globalmente
window.prevOctave = prevOctave;
window.nextOctave = nextOctave;
window.updateOctaveDisplay = updateOctaveDisplay;
window.handleMultiFingerData = handleMultiFingerData;
window.displayActiveNotes = displayActiveNotes;

console.log("🎹 Piano.js Multi-Finger cargado correctamente");