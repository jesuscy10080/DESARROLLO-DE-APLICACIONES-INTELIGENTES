// Detector de gestos para navegación de octavas

// Estado de gestos
const gestureState = {
    lastGesture: null,
    lastGestureTime: 0,
    gestureCooldown: 1000,  // ms entre gestos
    gestureActive: false
};

// Procesar resultado de gestos
function processGestureResult(data) {
    // Si no hay navegación, no hacer nada
    if (!data.navigation) return;
    
    const now = Date.now();
    
    // Evitar gestos demasiado frecuentes
    if (now - gestureState.lastGestureTime < gestureState.gestureCooldown) {
        return;
    }
    
    // Actualizar estado
    gestureState.lastGesture = data.navigation;
    gestureState.lastGestureTime = now;
    
    // Mostrar feedback visual
    showGestureFeedback(data.navigation);
    
    // Si hay cambio de octava, procesar
    if (data.octave_change && data.new_octave_offset !== undefined) {
        pianoConfig.currentOctaveOffset = data.new_octave_offset;
        updateOctaveDisplay();
    }
}

// Mostrar feedback visual del gesto
function showGestureFeedback(gesture) {
    // Destacar el icono correspondiente
    const leftIcon = document.querySelector('.gesture-icon.left');
    const rightIcon = document.querySelector('.gesture-icon.right');
    
    if (gesture === 'left') {
        leftIcon.classList.add('active');
        setTimeout(() => leftIcon.classList.remove('active'), 500);
    } else if (gesture === 'right') {
        rightIcon.classList.add('active');
        setTimeout(() => rightIcon.classList.remove('active'), 500);
    }
    
    // Actualizar texto de ayuda
    const helpText = document.querySelector('.help-text');
    helpText.textContent = gesture === 'left' ? 
        'Cambiando a octava anterior...' : 
        'Cambiando a octava siguiente...';
    
    // Restaurar texto después de un tiempo
    setTimeout(() => {
        helpText.textContent = 'Apunta a izquierda o derecha para cambiar octavas';
    }, 2000);
}