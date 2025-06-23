"""
Utilidades para detección de gestos
"""

import numpy as np

def is_pointing_gesture(landmarks):
    """
    Determina si la mano está haciendo un gesto de apuntar
    (dedo índice extendido, otros dedos cerrados) gesture_utils.py
    
    Args:
        landmarks: Puntos de referencia de la mano
        
    Returns:
        bool: True si está apuntando
    """
    try:
        # Verificar posición del dedo índice vs otros dedos
        index_tip_y = landmarks[8].y
        middle_tip_y = landmarks[12].y
        ring_tip_y = landmarks[16].y
        pinky_tip_y = landmarks[20].y
        
        # Índice debe estar más extendido (coordenada Y menor) que otros dedos
        return (index_tip_y < middle_tip_y - 0.05 and 
                index_tip_y < ring_tip_y - 0.05 and 
                index_tip_y < pinky_tip_y - 0.05)
    except Exception as e:
        print(f"Error en is_pointing_gesture: {e}")
        return False

def is_finger_extended(landmarks, finger_indices):
    """
    Determina si un dedo está extendido
    
    Args:
        landmarks: Puntos de referencia de la mano
        finger_indices: Índices del dedo a verificar
        
    Returns:
        bool: True si el dedo está extendido
    """
    try:
        # Punta y articulaciones del dedo
        tip = np.array([landmarks[finger_indices[0]].x, landmarks[finger_indices[0]].y])
        mcp = np.array([landmarks[finger_indices[3]].x, landmarks[finger_indices[3]].y])
        
        # Calcular distancia
        distance = np.linalg.norm(tip - mcp)
        
        # Un dedo extendido tiene mayor distancia desde la base
        return distance > 0.15  # Umbral basado en pruebas
    except Exception as e:
        print(f"Error en is_finger_extended: {e}")
        return False