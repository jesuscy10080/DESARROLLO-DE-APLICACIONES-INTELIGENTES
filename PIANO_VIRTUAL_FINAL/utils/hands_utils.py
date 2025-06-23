"""
Utilidades para procesamiento Multi-Finger
hands_utils.py - Versión simplificada para detección de múltiples dedos
"""

import numpy as np

def is_finger_up_simple(landmarks, finger_tip_idx, finger_pip_idx):
    """
    Detecta si un dedo está levantado (versión simplificada para multi-finger)
    Basada en tu código de referencia
    
    Args:
        landmarks: Lista de puntos de referencia de la mano
        finger_tip_idx: Índice de la punta del dedo
        finger_pip_idx: Índice de la articulación media del dedo
        
    Returns:
        bool: True si el dedo está levantado
    """
    try:
        return landmarks[finger_tip_idx].y < landmarks[finger_pip_idx].y
    except Exception as e:
        print(f"Error en is_finger_up_simple: {e}")
        return False

def is_thumb_up_simple(landmarks, hand_label):
    """
    Detecta si el pulgar está levantado (lógica especial como tu código de referencia)
    
    Args:
        landmarks: Lista de puntos de referencia de la mano
        hand_label: "Right" o "Left"
        
    Returns:
        bool: True si el pulgar está levantado
    """
    try:
        # Para mano derecha: pulgar a la derecha
        # Para mano izquierda: pulgar a la izquierda
        if hand_label == "Right":
            return landmarks[4].x > landmarks[3].x
        else:  # Left hand
            return landmarks[4].x < landmarks[3].x
    except Exception as e:
        print(f"Error en is_thumb_up_simple: {e}")
        return False

def get_note_from_finger_position(finger_x, finger_y, piano_config):
    """
    Determina qué nota corresponde a la posición de un dedo en el teclado virtual
    
    Args:
        finger_x: Coordenada X del dedo (normalizada 0-1)
        finger_y: Coordenada Y del dedo (normalizada 0-1)
        piano_config: Configuración del piano
        
    Returns:
        str: Nombre de la nota o None
    """
    try:
        # Solo detectar en la zona del teclado virtual (5% - 40% de la pantalla)
        if finger_y < 0.05 or finger_y > 0.40:
            return None
        
        # Extraer configuración
        min_octave = piano_config.get('min_octave', 2)
        visible_octaves = piano_config.get('visible_octaves', 3)
        current_octave_offset = piano_config.get('current_octave_offset', 1)
        max_octave = piano_config.get('max_octave', 6)
        
        # Notas por octava (12 semitonos)
        notes_per_octave = ['DO', 'DOS', 'RE', 'RES', 'MI', 'FA', 'FAS', 'SOL', 'SOLS', 'LA', 'LAS', 'SI']
        
        # Calcular octava inicial visible
        start_octave = min_octave + current_octave_offset
        
        # Calcular total de notas visibles
        total_notes = visible_octaves * len(notes_per_octave)
        note_width = 1.0 / total_notes
        
        # Determinar índice de nota basado en posición X
        note_index = int(finger_x / note_width)
        
        if note_index >= total_notes or note_index < 0:
            return None
        
        # Calcular octava y nota dentro de la octava
        octave_index = note_index // len(notes_per_octave)
        note_in_octave = note_index % len(notes_per_octave)
        
        current_octave = start_octave + octave_index
        
        # Verificar que no exceda la octava máxima
        if current_octave > max_octave:
            return None
        
        note_name = notes_per_octave[note_in_octave]
        return f"{note_name}{current_octave}"
        
    except Exception as e:
        print(f"Error en get_note_from_finger_position: {e}")
        return None

def detect_all_fingers_state(landmarks, hand_label):
    """
    Detecta el estado de todos los dedos de una mano
    Basado en tu código de referencia
    
    Args:
        landmarks: Puntos de referencia de la mano
        hand_label: "Right" o "Left"
        
    Returns:
        list: Lista de booleanos [pulgar, índice, medio, anular, meñique]
    """
    try:
        # Índices de puntas y articulaciones (como tu código de referencia)
        finger_tips = [4, 8, 12, 16, 20]  # Pulgar, Índice, Medio, Anular, Meñique
        finger_pips = [3, 6, 10, 14, 18]  # Articulaciones medias
        
        finger_states = []
        
        for i in range(5):
            if i == 0:  # Pulgar (lógica especial)
                finger_up = is_thumb_up_simple(landmarks, hand_label)
            else:  # Otros dedos
                finger_up = is_finger_up_simple(landmarks, finger_tips[i], finger_pips[i])
            
            finger_states.append(finger_up)
        
        return finger_states
        
    except Exception as e:
        print(f"Error en detect_all_fingers_state: {e}")
        return [False] * 5

def extract_finger_positions(landmarks):
    """
    Extrae las posiciones de todos los dedos
    
    Args:
        landmarks: Puntos de referencia de la mano
        
    Returns:
        list: Lista de diccionarios con posiciones de dedos
    """
    try:
        finger_tips = [4, 8, 12, 16, 20]  # Índices de puntas de dedos
        finger_names = ["Pulgar", "Índice", "Medio", "Anular", "Meñique"]
        
        finger_positions = []
        
        for i, (tip_idx, name) in enumerate(zip(finger_tips, finger_names)):
            finger_positions.append({
                'finger': name,
                'tip_index': tip_idx,
                'x': landmarks[tip_idx].x,
                'y': landmarks[tip_idx].y,
                'z': landmarks[tip_idx].z
            })
        
        return finger_positions
        
    except Exception as e:
        print(f"Error en extract_finger_positions: {e}")
        return []

# Funciones de compatibilidad con el código anterior (deprecadas pero mantenidas)
def is_finger_bent(landmarks, finger_indices=[8, 7, 6, 5], threshold_angle=120):
    """Función de compatibilidad - usa la nueva lógica simplificada"""
    try:
        # Usar lógica simplificada para compatibilidad
        tip_idx = finger_indices[0]
        pip_idx = finger_indices[1]
        return not is_finger_up_simple(landmarks, tip_idx, pip_idx)
    except:
        return False

def determine_note_from_position(landmarks, img_width, img_height, keyboard_config, **kwargs):
    """Función de compatibilidad - usa la nueva lógica"""
    try:
        # Obtener posición del dedo índice para compatibilidad
        finger_x = landmarks[8].x
        finger_y = landmarks[8].y
        
        # Convertir configuración del teclado a formato esperado
        piano_config = {
            'min_octave': keyboard_config.get('min_octave', 2),
            'visible_octaves': keyboard_config.get('visible_octaves', 3),
            'current_octave_offset': keyboard_config.get('current_octave_offset', 1),
            'max_octave': 6
        }
        
        return get_note_from_finger_position(finger_x, finger_y, piano_config)
        
    except Exception as e:
        print(f"Error en determine_note_from_position (compatibilidad): {e}")
        return None

def detect_navigation_gesture(landmarks):
    """Función de compatibilidad - navegación simplificada"""
    try:
        # Lógica básica de navegación (puedes mejorarla después)
        wrist = np.array([landmarks[0].x, landmarks[0].y])
        index_tip = np.array([landmarks[8].x, landmarks[8].y])
        
        # Calcular dirección
        direction = index_tip - wrist
        direction_normalized = direction / (np.linalg.norm(direction) + 1e-7)
        
        # Verificar si apunta horizontalmente
        if abs(direction_normalized[0]) > 0.7:
            if direction_normalized[0] < -0.7:
                return 'left'
            elif direction_normalized[0] > 0.7:
                return 'right'
        
        return None
    except:
        return None