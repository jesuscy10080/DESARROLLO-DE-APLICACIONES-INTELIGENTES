import cv2
import numpy as np

def create_transparent_keyboard(img, keyboard_config, is_playing=False, active_note=None):
    """
    Crea un teclado virtual con mayor transparencia Keyboboard_utils.js
    
    Args:
        img: Imagen base
        keyboard_config: Configuración del teclado
        is_playing: Si se está tocando una nota
        active_note: Nota activa
        
    Returns:
        numpy.ndarray: Imagen con teclado superpuesto
    """
    h, w = img.shape[:2]
    result = img.copy()
    
    # Extraer configuración
    keyboard_top = keyboard_config['top']
    min_octave = keyboard_config['min_octave']
    visible_octaves = keyboard_config['visible_octaves']
    current_octave_offset = keyboard_config['current_octave_offset']
    opacity = keyboard_config['opacity']
    
    # Altura del teclado (30% de la altura)
    keyboard_height = int(h * 0.3)
    keyboard_bottom = keyboard_top + keyboard_height
    
    # Fondo semitransparente
    overlay = np.zeros((keyboard_height, w, 3), dtype=np.uint8)  # Fondo negro
    
    # Aplicar transparencia
    roi = result[keyboard_top:keyboard_bottom, 0:w]
    if roi.shape[0] > 0 and roi.shape[1] > 0:
        cv2.addWeighted(overlay, opacity, roi, 1-opacity, 0, roi)
    
    # Dibujar borde
    border_color = (0, 255, 255) if is_playing else (0, 200, 200)  # Amarillo o cian
    cv2.rectangle(result, (0, keyboard_top), (w, keyboard_bottom), border_color, 2)
    
    # Dimensiones de teclas
    white_key_width = w // (7 * visible_octaves)
    black_key_width = white_key_width // 2
    black_key_height = keyboard_height * 2 // 3
    
    # Información de teclas negras
    black_key_positions = [0, 1, 3, 4, 5]
    black_key_names = ['DO#', 'RE#', 'FA#', 'SOL#', 'LA#']
    
    # Colores de notas más vibrantes
    NOTE_COLORS = {
        'DO': (0, 0, 255),    # Rojo
        'RE': (0, 128, 255),  # Naranja
        'MI': (0, 255, 255),  # Amarillo
        'FA': (0, 255, 0),    # Verde
        'SOL': (255, 0, 0),   # Azul
        'LA': (255, 0, 255),  # Magenta
        'SI': (128, 0, 255)   # Púrpura
    }
    
    # Dibujar octavas visibles
    for i in range(visible_octaves):
        octave_num = min_octave + current_octave_offset + i
        
        if octave_num > min_octave + 4:  # Máximo 5 octavas (2-6)
            break
            
        octave_x = i * 7 * white_key_width
        
        # Destacar el rango de octavas
        octave_text = f"Octava {octave_num}"
        cv2.putText(result, octave_text, 
                   (octave_x + 10, keyboard_top - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Dibujar teclas blancas
        for j in range(7):
            x1 = octave_x + j * white_key_width
            x2 = x1 + white_key_width
            y1 = keyboard_top
            y2 = keyboard_bottom
            
            # Obtener nota
            note_names = ['DO', 'RE', 'MI', 'FA', 'SOL', 'LA', 'SI']
            note_name = note_names[j]
            note_full = f"{note_name}{octave_num}"
            
            # Color de tecla (más transparente)
            key_color = (250, 250, 250)  # Blanco
            border_color = (100, 100, 100)  # Gris
            
            if active_note == note_full:
                key_color = NOTE_COLORS.get(note_name, (240, 240, 240))
                border_color = (50, 50, 50)
            
            # Dibujar tecla con transparencia
            key_overlay = np.ones((y2-y1, x2-x1, 3), dtype=np.uint8) * key_color
            roi = result[y1:y2, x1:x2]
            cv2.addWeighted(key_overlay, 0.3, roi, 0.7, 0, roi)
            cv2.rectangle(result, (x1, y1), (x2, y2), border_color, 1)
            
            # Nombre de nota
            font_size = 0.5
            text_color = (0, 0, 0)  # Negro
            text_thickness = 1
            
            if active_note == note_full:
                text_color = (0, 0, 255)  # Rojo
                text_thickness = 2
            
            # Centrar texto
            text_size = cv2.getTextSize(note_full, cv2.FONT_HERSHEY_SIMPLEX, font_size, text_thickness)[0]
            text_x = x1 + (white_key_width - text_size[0]) // 2
            text_y = y2 - 15
            
            cv2.putText(result, note_full, (text_x, text_y),
                      cv2.FONT_HERSHEY_SIMPLEX, font_size, text_color, text_thickness)
    
        # Dibujar teclas negras
        for idx, pos in enumerate(black_key_positions):
            x = octave_x + (pos + 1) * white_key_width - black_key_width // 2
            y1 = keyboard_top
            y2 = keyboard_top + black_key_height
            
            note_name = black_key_names[idx]
            note_full = f"{note_name}{octave_num}"
            
            # Color negro semitransparente
            key_color = (30, 30, 30)
            
            if active_note == note_full:
                base_note = note_name.replace('#', '')
                key_color = NOTE_COLORS.get(base_note[:2], (60, 60, 60))
            
            # Dibujar tecla
            key_overlay = np.ones((y2-y1, black_key_width, 3), dtype=np.uint8) * key_color
            roi = result[y1:y2, x:x+black_key_width]
            if roi.shape[0] > 0 and roi.shape[1] > 0:
                cv2.addWeighted(key_overlay, 0.5, roi, 0.5, 0, roi)
            cv2.rectangle(result, (x, y1), (x + black_key_width, y2), (0, 0, 0), 1)
            
            # Nombre de nota
            font_size = 0.4
            text_size = cv2.getTextSize(note_full, cv2.FONT_HERSHEY_SIMPLEX, font_size, 1)[0]
            text_x = x + (black_key_width - text_size[0]) // 2
            text_y = y1 + black_key_height - 10
            
            cv2.putText(result, note_full, (text_x, text_y),
                      cv2.FONT_HERSHEY_SIMPLEX, font_size, (255, 255, 255), 1)
    
    # Dibujar controles de navegación
    nav_height = 30
    nav_y = keyboard_bottom + 10
    
    # Indicador de octavas visibles
    start_octave = min_octave + current_octave_offset
    end_octave = min_octave + current_octave_offset + visible_octaves - 1
    if end_octave > min_octave + 4:
        end_octave = min_octave + 4
    
    octave_text = f"Octavas visibles: {start_octave}-{end_octave} (de 2-6)"
    cv2.putText(result, octave_text, (w//2 - 120, nav_y), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Instrucciones de navegación
    nav_text = "Apunta ← o → para cambiar octavas o usa botones"
    cv2.putText(result, nav_text, (w//2 - 150, nav_y + 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    # Indicador de nota activa
    if is_playing and active_note:
        cv2.putText(result, f"Tocando: {active_note}", (w//2 - 70, keyboard_top - 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    return result