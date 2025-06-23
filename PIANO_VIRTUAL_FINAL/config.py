import os

# Configuración de la aplicación
SECRET_KEY = os.urandom(24)
DEBUG = True

# Rutas de archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, 'public', 'sounds', 'notes')  # Actualizado a 'public'

# Configuración del piano
PIANO_OCTAVES = 5              # Total de octavas (2-6)
PIANO_MIN_OCTAVE = 2           # Octava mínima
PIANO_MAX_OCTAVE = 6           # Octava máxima
VISIBLE_OCTAVES = 3            # Número de octavas visibles
DEFAULT_OCTAVE_OFFSET = 1      # Octava inicial (3-4-5 visibles)
KEYBOARD_OPACITY = 0.6         # Transparencia del teclado

# Parámetros de detección
FINGER_BEND_THRESHOLD = 120    # Ángulo para considerar dedo doblado
FINGER_INDICES = [8, 7, 6, 5]  # Índices del dedo índice
GESTURE_THRESHOLD = 0.3        # Umbral para detectar gestos de navegación