#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Piano Virtual Invisible - Aplicación Principal
----------------------------------------------
Aplicación web para piano virtual con soporte de gestos usando WebSockets.
VERSIÓN CON MODELO PROFESIONAL INTEGRADO
"""

import os
import sys
import time
import numpy as np
import cv2
import mediapipe as mp
import pygame
import tensorflow as tf
import json
import joblib  # ✅ AGREGADO para cargar scaler y encoder profesional
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("⚠️ flask-cors no está instalado. Ejecuta: pip install flask-cors")
import base64
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

# ✅ RUTAS DEL MODELO ORIGINAL
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'models_test', 'piano_test_model.h5')
SCALER_PATH = os.path.join(BASE_DIR, 'ml', 'models_test', 'scaler_test.pkl')
ENCODER_PATH = os.path.join(BASE_DIR, 'ml', 'models_test', 'encoder_test.pkl')

# ✅ RUTAS DEL MODELO PROFESIONAL (NUEVO)
PROFESSIONAL_MODEL_DIR = os.path.join(BASE_DIR, 'ml', 'models_professional')
PROFESSIONAL_MODEL_PATH = os.path.join(PROFESSIONAL_MODEL_DIR, 'piano_finetuned_model.h5')
PROFESSIONAL_SCALER_PATH = os.path.join(PROFESSIONAL_MODEL_DIR, 'scaler_professional.pkl')
PROFESSIONAL_ENCODER_PATH = os.path.join(PROFESSIONAL_MODEL_DIR, 'encoder_professional.pkl')

# Si no tienes fine-tuned, usar el modelo inicial
if not os.path.exists(PROFESSIONAL_MODEL_PATH):
    PROFESSIONAL_MODEL_PATH = os.path.join(PROFESSIONAL_MODEL_DIR, 'piano_professional_model.h5')

# Otras rutas
AUDIO_DIR = os.path.join(BASE_DIR, 'dataset', 'dataset_audio')
JSON_DATA_DIR = os.path.join(BASE_DIR, 'captured_data')

# Verificar existencia de archivos
print(f"Verificando archivos:")
print(f"- Modelo original: {'✅ Existe' if os.path.exists(MODEL_PATH) else '❌ No existe'}")
print(f"- Modelo profesional: {'✅ Existe' if os.path.exists(PROFESSIONAL_MODEL_PATH) else '❌ No existe'}")
print(f"- Scaler profesional: {'✅ Existe' if os.path.exists(PROFESSIONAL_SCALER_PATH) else '❌ No existe'}")
print(f"- Encoder profesional: {'✅ Existe' if os.path.exists(PROFESSIONAL_ENCODER_PATH) else '❌ No existe'}")
print(f"- Audio: {'✅ Existe' if os.path.exists(AUDIO_DIR) else '❌ No existe'}")
print(f"- JSON Data: {'✅ Existe' if os.path.exists(JSON_DATA_DIR) else '❌ No existe'}")

# Inicializar pygame para audio
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Inicializar MediaPipe
try:
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    print("✅ MediaPipe inicializado correctamente")
except Exception as e:
    print(f"⚠️ Error inicializando MediaPipe: {e}")
    hands = None

# Crear aplicación Flask
app = Flask(__name__, 
            static_folder='public',
            static_url_path='/public',
            template_folder='templates')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Habilitar CORS si está disponible
if CORS_AVAILABLE:
    CORS(app)

# Inicializar SocketIO con modo threading
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Variables globales para ML original
model = None
scaler = None
label_encoder = None

# ✅ VARIABLES GLOBALES PARA MODELO PROFESIONAL (NUEVO)
model_professional = None
scaler_professional = None
label_encoder_professional = None

# ✅ FUNCIÓN PARA CARGAR MODELO PROFESIONAL (NUEVO)
def load_trained_professional_model():
    """Cargar el modelo profesional que entrenaste"""
    global model_professional, scaler_professional, label_encoder_professional
    
    print("\n🚀 CARGANDO TU MODELO PROFESIONAL ENTRENADO...")
    print("-" * 50)
    
    try:
        # Verificar archivos
        if not os.path.exists(PROFESSIONAL_MODEL_PATH):
            print(f"❌ Modelo no encontrado: {PROFESSIONAL_MODEL_PATH}")
            return False
        
        if not os.path.exists(PROFESSIONAL_SCALER_PATH):
            print(f"❌ Scaler no encontrado: {PROFESSIONAL_SCALER_PATH}")
            return False
            
        if not os.path.exists(PROFESSIONAL_ENCODER_PATH):
            print(f"❌ Encoder no encontrado: {PROFESSIONAL_ENCODER_PATH}")
            return False
        
        # Cargar modelo
        print(f"📥 Cargando modelo: {os.path.basename(PROFESSIONAL_MODEL_PATH)}")
        model_professional = tf.keras.models.load_model(PROFESSIONAL_MODEL_PATH, compile=False)
        
        # Recompilar para asegurar compatibilidad
        model_professional.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Cargar scaler
        print(f"📏 Cargando scaler...")
        scaler_professional = joblib.load(PROFESSIONAL_SCALER_PATH)
        
        # Cargar encoder
        print(f"🏷️ Cargando encoder...")
        label_encoder_professional = joblib.load(PROFESSIONAL_ENCODER_PATH)
        
        print(f"✅ MODELO PROFESIONAL CARGADO EXITOSAMENTE!")
        print(f"   📊 Input shape: {model_professional.input_shape}")
        print(f"   📊 Output shape: {model_professional.output_shape}")
        print(f"   📊 Parámetros: {model_professional.count_params():,}")
        print(f"   📊 Clases disponibles: {len(label_encoder_professional.classes_)}")
        print(f"   📝 Ejemplos: {', '.join(label_encoder_professional.classes_[:8])}...")
        
        # Realizar predicción de prueba
        print("🧪 Realizando predicción de prueba...")
        test_features = np.random.random((1, 63)).astype(np.float32)
        test_normalized = scaler_professional.transform(test_features)
        test_prediction = model_professional.predict(test_normalized, verbose=0)
        test_note_idx = np.argmax(test_prediction)
        test_note = label_encoder_professional.inverse_transform([test_note_idx])[0]
        test_confidence = float(test_prediction[0][test_note_idx])
        print(f"✅ Predicción de prueba exitosa: {test_note} ({test_confidence:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cargando modelo profesional: {e}")
        model_professional = None
        scaler_professional = None
        label_encoder_professional = None
        return False

# ✅ FUNCIÓN PARA PREDECIR CON MODELO PROFESIONAL (NUEVO)
def predict_with_professional_model(landmarks):
    """Predecir nota usando tu modelo profesional entrenado"""
    global model_professional, scaler_professional, label_encoder_professional
    
    if not all([model_professional, scaler_professional, label_encoder_professional]):
        return None, 0.0, "model_not_loaded"
    
    try:
        # Convertir landmarks a features (63 valores)
        features = []
        for landmark in landmarks:
            if hasattr(landmark, 'x'):  # MediaPipe landmark
                features.extend([landmark.x, landmark.y, landmark.z])
            else:  # Lista de coordenadas
                features.extend([landmark[0], landmark[1], landmark[2]])
        
        if len(features) != 63:
            return None, 0.0, "invalid_features"
        
        # Normalizar con tu scaler
        features_array = np.array([features], dtype=np.float32)
        features_normalized = scaler_professional.transform(features_array)
        
        # Predecir con tu modelo
        prediction = model_professional.predict(features_normalized, verbose=0)
        predicted_class = np.argmax(prediction[0])
        confidence = float(prediction[0][predicted_class])
        
        # Convertir a nota
        predicted_note = label_encoder_professional.inverse_transform([predicted_class])[0]
        
        return predicted_note, confidence, "professional_ml"
        
    except Exception as e:
        print(f"⚠️ Error en predicción profesional: {e}")
        return None, 0.0, "prediction_error"

# ✅ FUNCIÓN SIMPLIFICADA PARA CARGAR MODELO ORIGINAL
def load_model_safely(model_path):
    """Cargar modelo .h5 de forma simple"""
    if not os.path.exists(model_path):
        print(f"❌ Archivo de modelo no encontrado: {model_path}")
        return None
    
    try:
        print(f"🔄 Cargando modelo .h5: {os.path.basename(model_path)}")
        model = tf.keras.models.load_model(model_path)
        print("✅ Modelo .h5 cargado exitosamente")
        print(f"   📊 Capas: {len(model.layers)}")
        print(f"   📊 Parámetros: {model.count_params():,}")
        return model
    except Exception as e:
        print(f"❌ Error cargando modelo .h5: {e}")
        return None

# Función para crear scaler básico
def create_basic_scaler():
    """Crear un scaler básico para normalización estándar"""
    class BasicScaler:
        def __init__(self):
            self.mean_ = np.array([0.5] * 63)
            self.scale_ = np.array([0.3] * 63)
            
        def transform(self, X):
            return (X - self.mean_) / self.scale_
            
        def fit_transform(self, X):
            return self.transform(X)
    
    return BasicScaler()

# Función para crear label encoder básico
def create_basic_label_encoder(gesture_data):
    """Crear un label encoder básico desde los datos de gestos"""
    class BasicLabelEncoder:
        def __init__(self, labels):
            unique_labels = sorted(set(labels))
            self.classes_ = np.array(unique_labels)
            self.label_to_index = {label: i for i, label in enumerate(unique_labels)}
            
        def transform(self, labels):
            return np.array([self.label_to_index.get(label, 0) for label in labels])
            
        def inverse_transform(self, indices):
            return np.array([self.classes_[i] if i < len(self.classes_) else 'unknown' for i in indices])
    
    if gesture_data:
        labels = [g.get('target_note_or_chord', 'unknown') for g in gesture_data]
        return BasicLabelEncoder(labels)
    else:
        basic_labels = ['DO2', 'RE2', 'MI2', 'FA2', 'SOL2', 'LA2', 'SI2',
                       'DO3', 'RE3', 'MI3', 'FA3', 'SOL3', 'LA3', 'SI3',
                       'DO4', 'RE4', 'MI4', 'FA4', 'SOL4', 'LA4', 'SI4',
                       'DO5', 'RE5', 'MI5', 'FA5', 'SOL5', 'LA5', 'SI5']
        return BasicLabelEncoder(basic_labels)

# ✅ CARGAR MODELO ORIGINAL (MANTENIDO)
try:
    model = load_model_safely(MODEL_PATH)
    
    if model:
        print("✅ Modelo original cargado correctamente")
        
        if os.path.exists(SCALER_PATH):
            try:
                scaler = joblib.load(SCALER_PATH)
                print("✅ Scaler original cargado desde archivo")
            except Exception as e:
                print(f"⚠️ Error cargando scaler: {e}")
                scaler = create_basic_scaler()
                print("✅ Usando scaler básico")
        else:
            print("⚠️ Scaler no encontrado, creando uno básico...")
            scaler = create_basic_scaler()
            print("✅ Scaler básico creado")
            
        if os.path.exists(ENCODER_PATH):
            try:
                label_encoder = joblib.load(ENCODER_PATH)
                print(f"✅ Label encoder original cargado desde archivo con {len(label_encoder.classes_)} clases")
            except Exception as e:
                print(f"⚠️ Error cargando label encoder: {e}")
                label_encoder = None
        else:
            print("⚠️ Label encoder no encontrado, se creará desde los datos...")
            label_encoder = None
            
    else:
        print("⚠️ Modelo original no encontrado, funcionando sin predicción de ML")
        scaler = create_basic_scaler() 
        label_encoder = None
        
except Exception as e:
    print(f"❌ Error general cargando modelo original: {e}")
    model = None
    scaler = create_basic_scaler()
    label_encoder = None

# Cargar datos de gestos
def load_gesture_data_from_folder(data_dir):
    """Cargar todos los archivos JSON de gestos desde una carpeta"""
    gesture_data = []
    
    if not os.path.exists(data_dir):
        print(f"❌ Carpeta de datos no encontrada: {data_dir}")
        return gesture_data
    
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    if not json_files:
        print(f"❌ No se encontraron archivos JSON en: {data_dir}")
        return gesture_data
    
    print(f"📁 Encontrados {len(json_files)} archivos JSON")
    
    successful_loads = 0
    errors = 0
    
    for json_file in json_files:
        try:
            json_path = os.path.join(data_dir, json_file)
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            gesture_data.append(data)
            successful_loads += 1
        except Exception as e:
            errors += 1
    
    print(f"✅ Archivos cargados exitosamente: {successful_loads}")
    if errors > 0:
        print(f"❌ Errores: {errors}")
    
    return gesture_data

# Usar la nueva función
gesture_data = []
try:
    gesture_data = load_gesture_data_from_folder(JSON_DATA_DIR)
    if gesture_data:
        print(f"✅ Datos de gestos cargados: {len(gesture_data)} registros")
        
        # Mostrar estadísticas
        notas_unicas = set()
        for gesture in gesture_data:
            nota = gesture.get('target_note_or_chord', 'unknown')
            notas_unicas.add(nota)
        
        print(f"📊 Notas únicas: {len(notas_unicas)}")
        ejemplo_notas = list(notas_unicas)[:10]
        print(f"📝 Ejemplos: {', '.join(ejemplo_notas)}")
        
        # Crear label encoder desde los datos
        if label_encoder is None:
            print("🔄 Creando label encoder desde los datos...")
            label_encoder = create_basic_label_encoder(gesture_data)
            print(f"✅ Label encoder creado con {len(label_encoder.classes_)} clases")
    else:
        print("⚠️ No se pudieron cargar datos de gestos")
        if label_encoder is None:
            label_encoder = create_basic_label_encoder([])
            print("✅ Label encoder básico creado")
except Exception as e:
    print(f"❌ Error cargando datos de gestos: {e}")

# Variables globales
last_navigation_time = time.time()
navigation_cooldown = 1.0  # segundos entre cambios de octava

# Función para crear configuración del teclado
def create_keyboard_config(h, w, octave_offset):
    """
    Crea la configuración del teclado virtual
    
    Args:
        h: Altura de la imagen
        w: Ancho de la imagen
        octave_offset: Desplazamiento de octavas
        
    Returns:
        dict: Configuración del teclado
    """
    keyboard_top = int(h * 0.2)  # 20% desde arriba
    keyboard_height = int(h * 0.3)  # 30% de altura
    
    return {
        'top': keyboard_top,
        'bottom': keyboard_top + keyboard_height,
        'min_octave': 2,  # DO2-SI2
        'visible_octaves': 3,  # 3 octavas visibles simultáneamente
        'current_octave_offset': octave_offset  # Offset desde la octava mínima
    }

# Importar utilidades
sys.path.append(BASE_DIR)
try:
    from utils.hands_utils import is_finger_bent, determine_note_from_position, detect_navigation_gesture
    from utils.audio_utils import play_note, get_available_notes
    from utils.gesture_utils import is_pointing_gesture
    print("✅ Módulos de utilidades importados correctamente")
except Exception as e:
    print(f"❌ Error importando utilidades: {e}")
    import traceback
    traceback.print_exc()

# Rutas de la aplicación
@app.route('/')
def index():
    """Página principal con el piano"""
    piano_config = {
        'total_octaves': 5,          # 5 octavas (2-6)
        'min_octave': 2,             # Comenzar en octava 2
        'max_octave': 6,             # Hasta octava 6
        'visible_octaves': 3,        # 3 octavas visibles a la vez
        'current_octave_offset': 1   # Comenzar mostrando octavas 3-4-5
    }
    
    # Obtener notas disponibles
    available_notes = []
    for octave in range(2, 7):
        octave_dir = os.path.join(AUDIO_DIR, f"octava{octave}")
        if os.path.exists(octave_dir):
            octave_notes = [os.path.splitext(f)[0] for f in os.listdir(octave_dir) if f.endswith('.wav')]
            available_notes.extend(octave_notes)
    
    return render_template('index.html', piano_config=piano_config, available_notes=available_notes)

@app.route('/about')
def about():
    """Página de información"""
    return render_template('about.html')

@app.route('/test')
def test():
    """Ruta de prueba para verificar el servidor"""
    return f"""
    <h1>🎹 Piano Virtual IA - Estado del Sistema</h1>
    <ul>
        <li>Modelo Original: {'✅ Cargado' if model else '❌ No cargado'}</li>
        <li>Modelo Profesional: {'✅ Cargado' if model_professional else '❌ No cargado'}</li>
        <li>Scaler: {'✅ Disponible' if scaler else '❌ No disponible'}</li>
        <li>Label Encoder: {'✅ Disponible' if label_encoder else '❌ No disponible'}</li>
        <li>MediaPipe: {'✅ Inicializado' if hands else '❌ Error'}</li>
        <li>Pygame Audio: ✅ Inicializado</li>
        <li>Datos de Gestos: {'✅ ' + str(len(gesture_data)) + ' registros' if gesture_data else '❌ Sin datos'}</li>
    </ul>
    <p><a href="/">← Volver al Piano</a></p>
    """

# API básicas
@app.route('/api/notes', methods=['GET'])
def get_notes_api():
    """Obtiene la lista de notas disponibles"""
    notes = []
    for octave in range(2, 7):
        octave_dir = os.path.join(AUDIO_DIR, f"octava{octave}")
        if os.path.exists(octave_dir):
            octave_notes = [os.path.splitext(f)[0] for f in os.listdir(octave_dir) if f.endswith('.wav')]
            notes.extend(octave_notes)
    return jsonify({'notes': sorted(notes)})

# Eventos de WebSocket
@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    client_ip = request.remote_addr if request else "desconocido"
    print(f'🔌 Cliente conectado desde: {client_ip}')
    emit('status', {'message': 'Conectado al servidor'})

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    print('🔌 Cliente desconectado')

@socketio.on('process_frame')
def handle_process_frame(data):
    """
    Procesa un frame enviado por el cliente - VERSIÓN MEJORADA CON MODELO PROFESIONAL
    """
    global last_navigation_time
    
    try:
        print('📷 Procesando frame...')
        # Extraer datos
        image_data = data['image'].split(',')[1]
        octave_offset = int(data.get('octaveOffset', 1))
        
        # Decodificar imagen
        img_bytes = base64.b64decode(image_data)
        img_array = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # Voltear horizontalmente
        frame = cv2.flip(frame, 1)
        
        # Dimensiones
        h, w = frame.shape[:2]
        
        # Convertir a RGB para MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Procesar con MediaPipe
        results = hands.process(frame_rgb)
        
        # Preparar respuesta mejorada
        response = {
            'hand_detected': False,
            'is_playing': False,
            'note': None,
            'position': None,
            'navigation': None,
            'octave_change': False,
            'new_octave_offset': octave_offset,
            'coordinates': [],  # ✅ NUEVO: Coordenadas de la mano
            'confidence': 0.0,  # ✅ NUEVO: Confianza del modelo
            'method': 'none',   # ✅ NUEVO: Método usado
            'audio_success': False  # ✅ NUEVO: Si se reprodujo audio
        }
        
        # Verificar detección de manos
        if results.multi_hand_landmarks:
            response['hand_detected'] = True
            print('👋 Mano detectada')
            
            # Analizar landmarks
            landmarks = results.multi_hand_landmarks[0].landmark
            
            # ✅ NUEVO: Extraer coordenadas para mostrar
            coordinates = []
            for i, landmark in enumerate(landmarks):
                coord = {
                    'index': i,
                    'x': landmark.x * w,
                    'y': landmark.y * h,
                    'z': landmark.z
                }
                coordinates.append(coord)
            response['coordinates'] = coordinates
            print(f"📊 Coordenadas extraídas: {len(coordinates)} puntos")
            
            # Verificar navegación por gestos
            current_time = time.time()
            if current_time - last_navigation_time > navigation_cooldown:
                # Detectar gesto de navegación si el dedo índice está apuntando
                if is_pointing_gesture(landmarks):
                    navigation = detect_navigation_gesture(landmarks)
                    
                    if navigation:
                        response['navigation'] = navigation
                        print(f'🧭 Navegación detectada: {navigation}')
                        
                        # Calcular nuevo offset de octava
                        new_offset = octave_offset
                        if navigation == 'left' and octave_offset > 0:
                            new_offset = octave_offset - 1
                            response['octave_change'] = True
                        elif navigation == 'right' and octave_offset < 2:  # Max offset para 5 octavas
                            new_offset = octave_offset + 1
                            response['octave_change'] = True
                        
                        if response['octave_change']:
                            last_navigation_time = current_time
                            response['new_octave_offset'] = new_offset
            
            # Verificar si el dedo está doblado para tocar
            finger_indices = [8, 7, 6, 5]  # Dedo índice
            threshold_angle = 120
            
            response['is_playing'] = is_finger_bent(
                landmarks, 
                finger_indices=finger_indices,
                threshold_angle=threshold_angle
            )
            
            if response['is_playing']:
                print('🎹 Dedo doblado - tocando nota')
                
                # ✅ NUEVO: USAR MODELO PROFESIONAL PRIMERO
                predicted_note, confidence, method = predict_with_professional_model(landmarks)
                
                if predicted_note and confidence > 0.6:  # Umbral de confianza
                    response['note'] = predicted_note
                    response['confidence'] = confidence
                    response['method'] = method
                    print(f'🤖 Predicción profesional: {predicted_note} (confianza: {confidence:.3f})')
                else:
                    # ✅ FALLBACK: Usar método original
                    keyboard_config = create_keyboard_config(h, w, octave_offset)
                    
                    note = determine_note_from_position(
                      landmarks, w, h, keyboard_config, 
                      gesture_data=gesture_data,
                      model=model,  # Modelo original
                      scaler=scaler,
                      label_encoder=label_encoder
                    )
                    
                    response['note'] = note
                    response['confidence'] = 0.5  # Confianza moderada para fallback
                    response['method'] = 'fallback_original'
                    if note:
                        print(f'📍 Método original: {note}')
                
                # ✅ REPRODUCIR AUDIO si hay nota
                if response['note']:
                    print(f'🎵 Reproduciendo: {response["note"]}')
                    # Extraer octava del nombre de la nota
                    if response['note'] and response['note'][-1].isdigit():
                        octave = response['note'][-1]
                        octave_dir = f"octava{octave}"
                        audio_path = os.path.join(AUDIO_DIR, octave_dir)
                        success = play_note(response['note'], audio_path)
                        response['audio_success'] = success
                        if success:
                            print(f"🔊 Audio reproducido exitosamente: {response['note']}")
                        else:
                            print(f"⚠️ Error reproduciendo audio: {response['note']}")
                
                # Posición del dedo
                index_tip_x = landmarks[8].x * w
                index_tip_y = landmarks[8].y * h
                response['position'] = {'x': float(index_tip_x), 'y': float(index_tip_y)}
        
        # Enviar respuesta al cliente
        emit('frame_processed', response)
        
    except Exception as e:
        logger.error(f"Error procesando frame: {e}")
        emit('error', {'message': str(e)})

@socketio.on('play_note')
def handle_play_note(data):
    """Reproduce una nota musical"""
    try:
        note = data['note']
        print(f'🎵 Solicitud de reproducción de nota: {note}')
        
        # Extraer octava
        if note and note[-1].isdigit():
            octave = note[-1]
            octave_dir = f"octava{octave}"
            audio_path = os.path.join(AUDIO_DIR, octave_dir)
            success = play_note(note, audio_path)
            emit('note_played', {'note': note, 'success': success}, broadcast=True)
        else:
            emit('error', {'message': f'Formato de nota incorrecto: {note}'})
    except Exception as e:
        emit('error', {'message': f'Error al reproducir nota: {e}'})

# Al final de app.py
if __name__ == '__main__':
    try:
        print("\n🎹 Iniciando Piano Virtual Invisible con WebSockets...")
        
        # ✅ CARGAR MODELO PROFESIONAL
        professional_loaded = load_trained_professional_model()
        
        # ✅ MOSTRAR RESUMEN DEL SISTEMA MEJORADO
        print(f"\n📊 ESTADO DEL SISTEMA:")
        print(f"   🧠 Modelo original: {'✅ Cargado (.h5)' if model else '❌ No cargado'}")
        print(f"   🎯 Modelo profesional: {'✅ Cargado' if professional_loaded else '❌ No cargado'}")
        print(f"   📏 Scaler: {'✅ Disponible' if scaler else '❌ No disponible'}")
        print(f"   🏷️ Label encoder: {'✅ Disponible (' + str(len(label_encoder.classes_)) + ' clases)' if label_encoder else '❌ No disponible'}")
        print(f"   📊 Datos de gestos: {'✅ ' + str(len(gesture_data)) + ' registros' if gesture_data else '❌ Sin datos'}")
        
        # ✅ INFORMACIÓN DEL MODELO PROFESIONAL
        if professional_loaded:
            print(f"\n🎯 TU MODELO PROFESIONAL:")
            print(f"   📊 Clases: {len(label_encoder_professional.classes_)}")
            print(f"   📝 Ejemplos: {', '.join(label_encoder_professional.classes_[:8])}")
            print(f"   🔧 Input: (None, 63) - 21 landmarks × 3 coordenadas")
            print(f"   🎯 Umbral confianza: 60%")
            print(f"   🚀 Prioridad: ALTA (se usa primero)")
        else:
            print(f"\n⚠️ Modelo profesional no disponible - usando método original")
        
        # Verificar estructura de audio
        print(f"\n🎵 VERIFICANDO ARCHIVOS DE AUDIO...")
        total_audio_files = 0
        for octave in range(2, 7):
            octave_dir = os.path.join(AUDIO_DIR, f"octava{octave}")
            if os.path.exists(octave_dir):
                files = [f for f in os.listdir(octave_dir) if f.endswith('.wav')]
                total_audio_files += len(files)
                print(f"✅ Octava {octave}: {len(files)} archivos de audio")
            else:
                print(f"⚠️ Carpeta de octava{octave} no encontrada")
        
        print(f"📊 Total archivos de audio: {total_audio_files}")
        
        # Mostrar URL manualmente 
        print("\n🌐 Servidor disponible en: http://127.0.0.1:5000")
        print("🌐 Prueba esta ruta para verificar: http://127.0.0.1:5000/test")
        
        print(f"\n🎹 INSTRUCCIONES DE USO:")
        print(f"   1. Abre http://127.0.0.1:5000 en tu navegador")
        print(f"   2. Permite acceso a la cámara")
        print(f"   3. Pon tu mano frente a la cámara")
        print(f"   4. DOBLA tu dedo índice para 'tocar' una tecla")
        print(f"   5. El {'modelo profesional' if professional_loaded else 'sistema'} detectará el gesto")
        print(f"   6. Se reproducirá el audio de la nota correspondiente")
        print(f"   7. ¡Disfruta tu piano virtual con IA!")
        
        # Iniciar servidor (modo corregido para Windows)
        socketio.run(app, host='127.0.0.1', port=5000, debug=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"\n❌ ERROR AL INICIAR: {e}")
        import traceback
        traceback.print_exc()
        
        # Intentar iniciar en modo básico si fallan los WebSockets
        print("\n⚠️ Intentando iniciar en modo básico sin WebSockets...")
        try:
            app.run(host='127.0.0.1', port=5000, debug=True)
        except Exception as e:
            print(f"❌ ERROR TAMBIÉN EN MODO BÁSICO: {e}")