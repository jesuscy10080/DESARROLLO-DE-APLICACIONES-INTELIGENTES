"""
Rutas API para el Piano Virtual Invisible
"""

from flask import Blueprint, request, jsonify, current_app
import os

def register_api_routes(app):
    """Registra rutas API en la aplicación Flask"""
    
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    
    @api_bp.route('/notes', methods=['GET'])
    def get_notes():
        """Obtiene la lista de notas disponibles"""
        from public.utils.audio_utils import get_available_notes
        
        notes = []
        AUDIO_DIR = os.path.join(app.root_path, 'dataset', 'dataset_audio')
        
        for octave in range(2, 7):  # Octavas 2-6
            octave_dir = os.path.join(AUDIO_DIR, f"octava{octave}")
            if os.path.exists(octave_dir):
                octave_notes = [os.path.splitext(f)[0] for f in os.listdir(octave_dir) if f.endswith('.wav')]
                notes.extend(octave_notes)
        
        return jsonify({'notes': sorted(notes)})
    
    @api_bp.route('/play-note/<note>', methods=['GET'])
    def play_note_endpoint(note):
        """Reproduce una nota musical"""
        from public.utils.audio_utils import play_note
        
        AUDIO_DIR = os.path.join(app.root_path, 'dataset', 'dataset_audio')
        
        # Extraer octava
        if note and note[-1].isdigit():
            octave = note[-1]
            octave_dir = f"octava{octave}"
            audio_path = os.path.join(AUDIO_DIR, octave_dir)
            success = play_note(note, audio_path)
            
            if success:
                return jsonify({'status': 'success', 'note': note})
        
        return jsonify({'status': 'error', 'message': f'No se pudo reproducir la nota {note}'}), 404
    
    app.register_blueprint(api_bp)