"""
Utilidades para manejo de audio en el Piano Virtual
"""

import os
import pygame
import threading

def play_note(note, audio_dir):
    """
    Reproduce el sonido de una nota musical
    
    Args:
        note: Nota a reproducir (ej. "DO4")
        audio_dir: Directorio con archivos de audio
        
    Returns:
        bool: True si se reproduce correctamente
    """
    try:
        # Buscar el archivo de audio
        sound_path = None
        
        # Primero buscar directamente en el directorio de octava
        note_path = os.path.join(audio_dir, f"{note}.wav")
        if os.path.exists(note_path):
            sound_path = note_path
        
        # Si no se encuentra, buscar sin importar mayúsculas/minúsculas
        if not sound_path:
            for file in os.listdir(audio_dir):
                if file.lower() == f"{note.lower()}.wav":
                    sound_path = os.path.join(audio_dir, file)
                    break
        
        # Reproducir sonido
        if sound_path and os.path.exists(sound_path):
            sound = pygame.mixer.Sound(sound_path)
            sound.play()
            print(f"🎵 Reproduciendo: {note} desde {sound_path}")
            return True
        else:
            print(f"⚠️ No se encontró archivo de audio para {note} en {audio_dir}")
            return False
            
    except Exception as e:
        print(f"Error reproduciendo {note}: {e}")
        return False

def play_note_async(note, audio_dir):
    """Reproduce una nota en un hilo separado"""
    thread = threading.Thread(target=lambda: play_note(note, audio_dir))
    thread.daemon = True
    thread.start()
    return True

def get_available_notes(audio_dir):
    """Obtiene la lista de notas disponibles"""
    notes = []
    
    try:
        if os.path.exists(audio_dir):
            # Buscar en carpetas
            for octave in range(2, 7):  # Octavas 2-6
                octave_dir = os.path.join(audio_dir, f"octava{octave}")
                if os.path.exists(octave_dir):
                    octave_notes = [os.path.splitext(f)[0] for f in os.listdir(octave_dir) if f.endswith('.wav')]
                    notes.extend(octave_notes)
        
        return sorted(notes)
    except Exception as e:
        print(f"Error obteniendo notas disponibles: {e}")
        return []