#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎹 Capturador de Gestos de Piano con 3 Categorías
Aplicación completa para capturar gestos positivos, negativos y navegación
"""

import cv2
import mediapipe as mp
import numpy as np
import json
import os
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import pygame

class PianoCaptureApp:
    def __init__(self):
        # Inicializar MediaPipe - AMBAS MANOS
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,  # DETECTAR AMBAS MANOS
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Variables de captura - AMBAS MANOS
        self.cap = None
        self.capturing = False
        self.current_landmarks_left = []   
        self.current_landmarks_right = []  
        self.sample_count = 0
        
        # ✅ CONFIGURACIÓN NUEVA: 3 CATEGORÍAS + 120 MUESTRAS
        self.current_octave = 4
        self.current_category = "POSITIVE"  # POSITIVE, NEGATIVE, NAVIGATION
        self.current_note = "DO"
        self.current_gesture_type = "single"
        self.current_chord = "Mayor"
        self.target_samples = 120  # ✅ CAMBIADO DE 30 A 120
        
        # Crear directorio de datos
        self.data_dir = "captured_data_3categories"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Definiciones de notas y categorías
        self.setup_musical_definitions()
        
        # Inicializar GUI
        self.setup_gui()
        
    def setup_musical_definitions(self):
        """Definir todas las categorías, notas y acordes disponibles"""
        # ✅ CATEGORÍAS PRINCIPALES
        self.categories = {
            "POSITIVE": "🎵 Gestos Positivos (Notas/Acordes)",
            "NEGATIVE": "❌ Gestos Negativos (No tocar)",
            "NAVIGATION": "🧭 Navegación (Izquierda/Derecha)"
        }
        
        # Notas cromáticas
        self.notes_chromatic = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"]
        self.notes_display = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"]
        self.octaves = [2, 3, 4, 5, 6]
        
        # ✅ GESTOS NEGATIVOS
        self.negative_gestures = {
            "HAND_OPEN": "Mano abierta (dedos extendidos)",
            "FIST_CLOSED": "Puño cerrado (todos los dedos)",
            "PARTIAL_BEND": "Dedos parcialmente doblados",
            "TRANSITION": "Movimiento entre teclas",
            "WRONG_FINGERS": "Dedos incorrectos doblados",
            "OUT_OF_ZONE": "Mano fuera de zona piano",
            "MULTIPLE_FINGERS": "Múltiples dedos doblados",
            "THUMB_ONLY": "Solo pulgar doblado",
            "PINCH_GESTURE": "Gesto de pellizco/agarre"
        }
        
        # ✅ GESTOS DE NAVEGACIÓN
        self.navigation_gestures = {
            "NAVIGATE_LEFT": "Apuntar hacia la izquierda",
            "NAVIGATE_RIGHT": "Apuntar hacia la derecha", 
            "NAVIGATE_NEUTRAL": "Índice extendido (neutral)"
        }
        
        # Definiciones de acordes (mantener original)
        self.chord_definitions = {
            "chord-2": {
                "Tercera Mayor": [0, 4],      # DO-MI
                "Tercera Menor": [0, 3],      # DO-MI♭
                "Quinta": [0, 7],             # DO-SOL
                "Octava": [0, 12],            # DO-DO siguiente
                "Segunda": [0, 2],            # DO-RE
                "Cuarta": [0, 5],             # DO-FA
            },
            "chord-3": {
                "Mayor": [0, 4, 7],           # DO-MI-SOL
                "Menor": [0, 3, 7],           # DO-MI♭-SOL
                "Disminuido": [0, 3, 6],      # DO-MI♭-SOL♭
                "Sus4": [0, 5, 7],            # DO-FA-SOL
                "Sus2": [0, 2, 7],            # DO-RE-SOL
            },
            "chord-4": {
                "Mayor 7": [0, 4, 7, 11],     # DO-MI-SOL-SI
                "Menor 7": [0, 3, 7, 10],     # DO-MI♭-SOL-SI♭
                "Dominante 7": [0, 4, 7, 10], # DO-MI-SOL-SI♭
                "Mayor 6": [0, 4, 7, 9],      # DO-MI-SOL-LA
            },
            "chord-5": {
                "Mayor 9": [0, 4, 7, 11, 14], # DO-MI-SOL-SI-RE
                "Menor 9": [0, 3, 7, 10, 14], # DO-MI♭-SOL-SI♭-RE
                "Pentatónica": [0, 2, 4, 7, 9], # DO-RE-MI-SOL-LA
            }
        }
        
    def setup_gui(self):
        """Crear interfaz gráfica con tkinter"""
        self.root = tk.Tk()
        self.root.title("🎹 Capturador de Gestos - 3 Categorías")
        self.root.geometry("450x700")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="🎹 Capturador 3 Categorías", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # ✅ SELECTOR DE CATEGORÍA PRINCIPAL
        ttk.Label(main_frame, text="Categoría Principal:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar(value="POSITIVE")
        category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, 
                                    values=list(self.categories.keys()), width=15)
        category_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        category_combo.bind("<<ComboboxSelected>>", self.on_category_change)
        
        # ✅ DESCRIPCIÓN DE CATEGORÍA
        self.category_desc = ttk.Label(main_frame, text=self.categories["POSITIVE"], 
                                     font=("Arial", 9), foreground="darkblue")
        self.category_desc.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Configuración de octava (solo para POSITIVE)
        ttk.Label(main_frame, text="Octava:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.octave_var = tk.StringVar(value="4")
        self.octave_combo = ttk.Combobox(main_frame, textvariable=self.octave_var, values=["2", "3", "4", "5", "6"])
        self.octave_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        self.octave_combo.bind("<<ComboboxSelected>>", self.on_octave_change)
        
        # Tipo de gesto (solo para POSITIVE)
        ttk.Label(main_frame, text="Tipo de Gesto:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.gesture_type_var = tk.StringVar(value="single")
        self.gesture_combo = ttk.Combobox(main_frame, textvariable=self.gesture_type_var, 
                                       values=["single", "chord-2", "chord-3", "chord-4", "chord-5"])
        self.gesture_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        self.gesture_combo.bind("<<ComboboxSelected>>", self.on_gesture_type_change)
        
        # ✅ SELECTOR DINÁMICO (Nota/Gesto Negativo/Navegación)
        ttk.Label(main_frame, text="Objetivo:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.target_var = tk.StringVar(value="DO")
        self.target_combo = ttk.Combobox(main_frame, textvariable=self.target_var, values=self.notes_display)
        self.target_combo.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Información de captura
        info_frame = ttk.LabelFrame(main_frame, text="Estado de Captura", padding="10")
        info_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 10))
        
        self.status_label = ttk.Label(info_frame, text="Cámara desconectada", foreground="red")
        self.status_label.pack()
        
        self.sample_label = ttk.Label(info_frame, text="Muestras: 0/120")  # ✅ CAMBIADO A 120
        self.sample_label.pack()
        
        self.quality_label = ttk.Label(info_frame, text="Calidad: ---")
        self.quality_label.pack()
        
        # Botones de control
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        self.start_camera_btn = ttk.Button(button_frame, text="🎥 Iniciar Cámara", command=self.start_camera)
        self.start_camera_btn.pack(side=tk.LEFT, padx=5)
        
        self.capture_btn = ttk.Button(button_frame, text="📸 Capturar Gesto", command=self.capture_gesture, state="disabled")
        self.capture_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹️ Detener", command=self.stop_camera, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=350, mode='determinate')
        self.progress.grid(row=8, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # ✅ INSTRUCCIONES DINÁMICAS
        self.instructions_text = ""
        self.inst_label = ttk.Label(main_frame, text="", justify=tk.LEFT, 
                              font=("Arial", 9), foreground="darkblue")
        self.inst_label.grid(row=9, column=0, columnspan=2, pady=10)
        
        # Configurar grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # ✅ INICIALIZAR
        self.on_category_change()
        
    def on_category_change(self, event=None):
        """Cambiar categoría principal y actualizar interfaz"""
        self.current_category = self.category_var.get()
        
        # Actualizar descripción
        self.category_desc.config(text=self.categories[self.current_category])
        
        # ✅ CONFIGURAR INTERFAZ SEGÚN CATEGORÍA
        if self.current_category == "POSITIVE":
            # Mostrar controles de notas/acordes
            self.octave_combo.config(state="normal")
            self.gesture_combo.config(state="normal")
            self.target_combo['values'] = self.notes_display
            self.target_var.set("DO")
            
        elif self.current_category == "NEGATIVE":
            # Ocultar octava y acordes, mostrar gestos negativos
            self.octave_combo.config(state="disabled")
            self.gesture_combo.config(state="disabled")
            self.target_combo['values'] = list(self.negative_gestures.keys())
            self.target_var.set("HAND_OPEN")
            
        elif self.current_category == "NAVIGATION":
            # Ocultar octava y acordes, mostrar navegación
            self.octave_combo.config(state="disabled") 
            self.gesture_combo.config(state="disabled")
            self.target_combo['values'] = list(self.navigation_gestures.keys())
            self.target_var.set("NAVIGATE_LEFT")
        
        # Actualizar instrucciones
        self.update_instructions()
        
    def on_octave_change(self, event=None):
        """Actualizar octava seleccionada"""
        if self.current_category == "POSITIVE":
            self.current_octave = int(self.octave_var.get())
        self.update_instructions()
        
    def on_gesture_type_change(self, event=None):
        """Actualizar tipo de gesto y opciones disponibles"""
        if self.current_category == "POSITIVE":
            self.current_gesture_type = self.gesture_type_var.get()
            
            if self.current_gesture_type == "single":
                self.target_combo['values'] = self.notes_display
                self.target_var.set("DO")
            else:
                chord_names = list(self.chord_definitions[self.current_gesture_type].keys())
                self.target_combo['values'] = chord_names
                self.target_var.set(chord_names[0])
        
        self.update_instructions()
            
    def update_instructions(self):
        """Actualizar instrucciones según categoría seleccionada"""
        category = self.current_category
        target = self.target_var.get()
        
        if category == "POSITIVE":
            self.instructions_text = f"""
📋 GESTOS POSITIVOS - {target}{self.current_octave}:
• Pon tu dedo índice doblado SOBRE la tecla {target}
• Para acordes: usa ambas manos simultáneamente
• Otros dedos pueden estar extendidos
• Mantén posición estable 1 segundo
• ✅ Calidad >70% para capturar
• Meta: 120 muestras de esta nota/acorde

🎹 OBJETIVO: Entrenar detección precisa de notas
🔄 Varía: ángulos, distancia, velocidad gesto
            """
            
        elif category == "NEGATIVE":
            gesture_desc = self.negative_gestures.get(target, "Gesto negativo")
            self.instructions_text = f"""
❌ GESTOS NEGATIVOS - {target}:
• {gesture_desc}
• La IA NO debe detectar ninguna nota
• Mantén gesto natural por 1 segundo
• Puedes estar en zona del piano o fuera
• ✅ Calidad >50% para capturar
• Meta: 120 muestras de este gesto negativo

🎯 OBJETIVO: Enseñar cuándo NO tocar
📝 IMPORTANTE: Variar posiciones y tipos
            """
            
        elif category == "NAVIGATION":
            gesture_desc = self.navigation_gestures.get(target, "Navegación")
            self.instructions_text = f"""
🧭 NAVEGACIÓN - {target}:
• {gesture_desc}
• Dedo índice EXTENDIDO (no doblado)
• Dirección clara hacia izq/der/adelante
• Otros dedos cerrados o semi-cerrados
• ✅ Calidad >60% para capturar
• Meta: 120 muestras de este gesto

🎯 OBJETIVO: Navegación rápida entre octavas
⚡ RESULTADO: Cambio automático de octava
            """
        
        if hasattr(self, 'inst_label'):
            self.inst_label.config(text=self.instructions_text)
        
    def start_camera(self):
        """Iniciar cámara y detección"""
        try:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            if not self.cap.isOpened():
                raise Exception("No se pudo abrir la cámara")
                
            self.capturing = True
            self.status_label.config(text="Cámara activa", foreground="green")
            self.start_camera_btn.config(state="disabled")
            self.capture_btn.config(state="normal")
            self.stop_btn.config(state="normal")
            
            # Iniciar hilo de captura
            self.camera_thread = Thread(target=self.camera_loop, daemon=True)
            self.camera_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar cámara: {str(e)}")
            
    def camera_loop(self):
        """Loop principal de la cámara"""
        while self.capturing and self.cap is not None:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            frame = cv2.resize(frame, (1280, 720))
            frame = cv2.flip(frame, 1)  # Efecto espejo
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            rgb_frame.flags.writeable = False
            results = self.hands.process(rgb_frame)
            rgb_frame.flags.writeable = True
            
            # ✅ DIBUJAR INTERFAZ SEGÚN CATEGORÍA
            frame = self.draw_category_interface(frame)
            
            # Procesar landmarks de ambas manos
            quality_score = 0
            quality_left = 0
            quality_right = 0
            self.current_landmarks_left = []
            self.current_landmarks_right = []
            
            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    hand_label = handedness.classification[0].label
                    
                    landmarks_array = []
                    for landmark in hand_landmarks.landmark:
                        landmarks_array.append([landmark.x, landmark.y, landmark.z])
                    
                    if hand_label == "Right":  
                        color = (0, 150, 255)  # Naranja para mano derecha
                        self.current_landmarks_right = landmarks_array
                        hand_display = "DERECHA"
                    else:  
                        color = (255, 100, 0)  # Azul para mano izquierda
                        self.current_landmarks_left = landmarks_array
                        hand_display = "IZQUIERDA"
                    
                    self.draw_colored_landmarks(frame, hand_landmarks, color, hand_display)
                    
                # Calcular calidad
                quality_left = self.calculate_quality(self.current_landmarks_left) if self.current_landmarks_left else 0
                quality_right = self.calculate_quality(self.current_landmarks_right) if self.current_landmarks_right else 0
                quality_score = max(quality_left, quality_right)
                
                self.draw_info_on_frame(frame, quality_score, quality_left, quality_right)
            else:
                self.draw_info_on_frame(frame, 0, 0, 0)
                
            # Actualizar GUI
            self.root.after(0, self.update_quality_label, quality_score, quality_left, quality_right)
            
            # Mostrar frame
            cv2.imshow('🎹 Piano Capture 3 Categorías - ESPACIO para capturar', frame)
            
            # Captura con espacio
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                self.capture_gesture()
            elif key == ord('q'):
                break
                
        cv2.destroyAllWindows()
        
    def draw_category_interface(self, frame):
        """Dibujar interfaz específica según categoría"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        if self.current_category == "POSITIVE":
            # Dibujar teclado de piano para notas
            frame = self.draw_piano_keyboard(frame)
            
        elif self.current_category == "NEGATIVE":
            # Dibujar área libre para gestos negativos
            self.draw_negative_gesture_area(overlay, w, h)
            
        elif self.current_category == "NAVIGATION":
            # Dibujar indicadores de navegación
            self.draw_navigation_indicators(overlay, w, h)
            
        return frame
        
    def draw_piano_keyboard(self, frame):
        """Dibujar teclado de piano para gestos positivos"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        margin = w // 10
        keyboard_width = w - (2 * margin)
        keyboard_height = 150
        keyboard_y = 40
        keyboard_x = margin
        
        current_octave = self.current_octave
        white_keys = ["DO", "RE", "MI", "FA", "SOL", "LA", "SI"]
        total_white_keys = 7
        white_key_width = keyboard_width // total_white_keys
        white_key_height = keyboard_height
        black_key_width = int(white_key_width * 0.7)
        black_key_height = int(keyboard_height * 0.65)
        
        # Dibujar teclas blancas
        for i, note in enumerate(white_keys):
            x = keyboard_x + (i * white_key_width)
            note_with_octave = f"{note}{current_octave}"
            
            if self.is_target_key(note, current_octave):
                color = (0, 255, 0)
                thickness = 6
            else:
                color = (255, 255, 255)
                thickness = 3
                
            cv2.rectangle(overlay, (x + 2, keyboard_y), 
                         (x + white_key_width - 2, keyboard_y + white_key_height), 
                         color, thickness)
            
            text_y = keyboard_y + white_key_height + 30
            cv2.putText(overlay, note_with_octave, 
                       (x + 8, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Dibujar teclas negras
        black_key_positions = [0.5, 1.5, 3.5, 4.5, 5.5]
        black_notes = ["DO#", "RE#", "FA#", "SOL#", "LA#"]
        
        for i, (relative_pos, note) in enumerate(zip(black_key_positions, black_notes)):
            x = keyboard_x + int(relative_pos * white_key_width + white_key_width // 2 - black_key_width // 2)
            note_with_octave = f"{note}{current_octave}"
            
            is_target = self.is_target_key(note, current_octave)
            
            if is_target:
                color = (0, 220, 0)
                thickness = 5
            else:
                color = (30, 30, 30)
                thickness = -1
                
            cv2.rectangle(overlay, (x, keyboard_y), 
                         (x + black_key_width, keyboard_y + black_key_height), 
                         color, thickness)
            
            text_color = (255, 255, 255) if is_target else (180, 180, 180)
            cv2.putText(overlay, note_with_octave, 
                       (x + 5, keyboard_y + black_key_height // 2 + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, text_color, 2)
        
        alpha = 0.6
        frame = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)
        return frame
        
    def draw_negative_gesture_area(self, overlay, w, h):
        """Dibujar área para gestos negativos"""
        # Área central libre
        area_margin = w // 8
        area_y = h // 4
        area_height = h // 2
        
        # Marco del área de gestos negativos
        cv2.rectangle(overlay, (area_margin, area_y), 
                     (w - area_margin, area_y + area_height), 
                     (0, 0, 255), 3)  # Rojo para negativos
        
        # Título
        cv2.putText(overlay, "AREA GESTOS NEGATIVOS", 
                   (area_margin + 20, area_y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Instrucciones específicas
        target = self.target_var.get()
        if target in self.negative_gestures:
            instruction = self.negative_gestures[target]
            cv2.putText(overlay, instruction, 
                       (area_margin + 20, area_y + 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
    def draw_navigation_indicators(self, overlay, w, h):
        """Dibujar indicadores para navegación"""
        center_x = w // 2
        center_y = h // 2
        
        target = self.target_var.get()
        
        if target == "NAVIGATE_LEFT":
            # Flecha izquierda grande
            points = np.array([[center_x - 100, center_y], 
                              [center_x - 50, center_y - 50], 
                              [center_x - 50, center_y + 50]], np.int32)
            cv2.fillPoly(overlay, [points], (255, 255, 0))  # Amarillo
            cv2.putText(overlay, "APUNTA IZQUIERDA", 
                       (center_x - 150, center_y + 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            
        elif target == "NAVIGATE_RIGHT":
            # Flecha derecha grande
            points = np.array([[center_x + 100, center_y], 
                              [center_x + 50, center_y - 50], 
                              [center_x + 50, center_y + 50]], np.int32)
            cv2.fillPoly(overlay, [points], (255, 255, 0))  # Amarillo
            cv2.putText(overlay, "APUNTA DERECHA", 
                       (center_x - 50, center_y + 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            
        elif target == "NAVIGATE_NEUTRAL":
            # Círculo central
            cv2.circle(overlay, (center_x, center_y), 50, (255, 255, 0), -1)
            cv2.putText(overlay, "INDICE ADELANTE", 
                       (center_x - 100, center_y + 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        
    def is_target_key(self, note, octave):
        """Verificar si una tecla es la tecla objetivo"""
        if self.current_category != "POSITIVE":
            return False
            
        target = self.target_var.get()
        target_octave = self.current_octave
        
        if octave != target_octave:
            return False
            
        if self.current_gesture_type == "single":
            return note == target
        else:
            # Para acordes
            if target in self.chord_definitions[self.current_gesture_type]:
                chord_intervals = self.chord_definitions[self.current_gesture_type][target]
                base_index = self.notes_chromatic.index("DO")
                chord_notes = []
                for interval in chord_intervals:
                    note_index = (base_index + interval) % 12
                    chord_notes.append(self.notes_chromatic[note_index])
                return note in chord_notes
        return False
        
    def draw_colored_landmarks(self, frame, hand_landmarks, color, hand_label):
        """Dibujar landmarks con colores específicos"""
        h, w = frame.shape[:2]
        
        # Dibujar conexiones
        connections = self.mp_hands.HAND_CONNECTIONS
        for connection in connections:
            start_idx = connection[0]
            end_idx = connection[1]
            
            start_point = hand_landmarks.landmark[start_idx]
            end_point = hand_landmarks.landmark[end_idx]
            
            start_pixel = (int(start_point.x * w), int(start_point.y * h))
            end_pixel = (int(end_point.x * w), int(end_point.y * h))
            
            cv2.line(frame, start_pixel, end_pixel, color, 3)
        
        # Dibujar puntos
        for idx, landmark in enumerate(hand_landmarks.landmark):
            pixel_coords = (int(landmark.x * w), int(landmark.y * h))
            
            if idx in [4, 8, 12, 16, 20]:  # Puntas de dedos
                radius = 12
                cv2.circle(frame, pixel_coords, radius, color, -1)
                cv2.circle(frame, pixel_coords, radius, (255, 255, 255), 3)
                cv2.putText(frame, str(idx), (pixel_coords[0]-8, pixel_coords[1]+5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            elif idx == 0:  # Muñeca
                radius = 10
                cv2.circle(frame, pixel_coords, radius, color, -1)
                cv2.circle(frame, pixel_coords, radius, (255, 255, 255), 2)
            else:
                radius = 6
                cv2.circle(frame, pixel_coords, radius, color, -1)
        
        # Etiqueta de mano
        if hand_landmarks.landmark:
            wrist = hand_landmarks.landmark[0]
            wrist_pixel = (int(wrist.x * w), int(wrist.y * h - 40))
            
            text_size = cv2.getTextSize(hand_label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            cv2.rectangle(frame, (wrist_pixel[0]-5, wrist_pixel[1]-25), 
                         (wrist_pixel[0] + text_size[0] + 5, wrist_pixel[1] + 5), (0, 0, 0), -1)
            
            cv2.putText(frame, hand_label, wrist_pixel, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
    def draw_info_on_frame(self, frame, quality, quality_left, quality_right):
        """Dibujar información de estado en el frame"""
        h, w = frame.shape[:2]
        
        # Información de objetivo
        category_text = f"Categoria: {self.current_category}"
        target_text = f"Objetivo: {self.target_var.get()}"
        
        cv2.putText(frame, category_text, (10, h - 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, target_text, (10, h - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Calidad por mano
        left_text = f"Izq: {quality_left:.1f}%"
        left_color = (255, 100, 0) if quality_left > 70 else (0, 255, 255) if quality_left > 50 else (100, 100, 100)
        cv2.putText(frame, left_text, (10, h - 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, left_color, 2)
        
        right_text = f"Der: {quality_right:.1f}%"
        right_color = (0, 150, 255) if quality_right > 70 else (0, 255, 255) if quality_right > 50 else (100, 100, 100)
        cv2.putText(frame, right_text, (150, h - 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, right_color, 2)
        
        # Calidad general
        general_color = (0, 255, 0) if quality > 70 else (0, 255, 255) if quality > 50 else (0, 0, 255)
        cv2.putText(frame, f"Calidad: {quality:.1f}%", (10, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, general_color, 2)
        
        # Muestras
        samples_text = f"Muestras: {self.sample_count}/{self.target_samples}"
        cv2.putText(frame, samples_text, (10, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Instrucciones dinámicas
        if self.current_category == "POSITIVE" and quality > 70:
            cv2.putText(frame, "CALIDAD OK - Presiona ESPACIO para capturar", 
                       (w//2 - 250, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        elif self.current_category == "NEGATIVE" and quality > 50:
            cv2.putText(frame, "GESTO NEGATIVO OK - Presiona ESPACIO", 
                       (w//2 - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        elif self.current_category == "NAVIGATION" and quality > 60:
            cv2.putText(frame, "NAVEGACION OK - Presiona ESPACIO", 
                       (w//2 - 180, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        else:
            cv2.putText(frame, "Mejora posicion segun instrucciones", 
                       (w//2 - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 100), 2)
                       
    def calculate_quality(self, landmarks):
        """Calcular calidad de detección"""
        if not landmarks or len(landmarks) != 21:
            return 0
            
        scores = []
        
        # Completitud de landmarks
        visible_count = sum(1 for lm in landmarks if lm[2] > -0.15)
        completeness = (visible_count / 21) * 100
        scores.append(completeness)
        
        # Estabilidad
        prev_attr = 'prev_landmarks_left' if len(landmarks) > 0 else 'prev_landmarks_right'
        if hasattr(self, prev_attr) and getattr(self, prev_attr):
            prev_landmarks = getattr(self, prev_attr)
            movement = 0
            for i, (current, prev) in enumerate(zip(landmarks, prev_landmarks)):
                dist = np.sqrt((current[0] - prev[0])**2 + (current[1] - prev[1])**2)
                movement += dist
            stability = max(0, 100 - movement * 800)
            scores.append(stability)
        else:
            scores.append(85)
            
        # Posición
        center_x = np.mean([lm[0] for lm in landmarks])
        center_y = np.mean([lm[1] for lm in landmarks])
        
        position_score = 100
        if center_x < 0.1 or center_x > 0.9:
            position_score -= 15
        if center_y < 0.25 or center_y > 0.95:
            position_score -= 10
            
        scores.append(max(0, position_score))
        
        # Dedos visibles
        finger_tips = [4, 8, 12, 16, 20]
        finger_quality = 0
        for tip_idx in finger_tips:
            if tip_idx < len(landmarks):
                tip_landmark = landmarks[tip_idx]
                if tip_landmark[2] > -0.1:
                    finger_quality += 20
        
        finger_score = min(100, finger_quality)
        scores.append(finger_score)
        
        # Guardar para siguiente frame
        if center_x < 0.5:
            self.prev_landmarks_left = landmarks.copy()
        else:
            self.prev_landmarks_right = landmarks.copy()
            
        # Promedio ponderado
        weighted_score = (
            scores[0] * 0.3 +  # Completitud
            scores[1] * 0.2 +  # Estabilidad
            scores[2] * 0.2 +  # Posición
            scores[3] * 0.3    # Dedos
        )
        
        return weighted_score
        
    def update_quality_label(self, quality, quality_left=0, quality_right=0):
        """Actualizar etiqueta de calidad en GUI"""
        color = "green" if quality > 70 else "orange" if quality > 50 else "red"
        self.quality_label.config(text=f"Calidad: {quality:.1f}% (Izq:{quality_left:.0f}% Der:{quality_right:.0f}%)", foreground=color)
        
    def capture_gesture(self):
        """Capturar gesto actual según categoría"""
        # Verificar detección de manos
        if not self.current_landmarks_left and not self.current_landmarks_right:
            messagebox.showwarning("Advertencia", "No se detectan manos. Posiciona tus manos frente a la cámara.")
            return
            
        # Calcular calidad
        quality_left = self.calculate_quality(self.current_landmarks_left) if self.current_landmarks_left else 0
        quality_right = self.calculate_quality(self.current_landmarks_right) if self.current_landmarks_right else 0
        overall_quality = max(quality_left, quality_right)
        
        # ✅ UMBRALES DIFERENTES POR CATEGORÍA
        min_quality = 70 if self.current_category == "POSITIVE" else 50 if self.current_category == "NEGATIVE" else 60
        
        if overall_quality < min_quality:
            messagebox.showwarning("Advertencia", f"Calidad muy baja ({overall_quality:.1f}%). Necesitas >{min_quality}%.")
            return
            
        # ✅ CREAR DATOS SEGÚN CATEGORÍA
        gesture_data = {
            "timestamp": datetime.now().isoformat(),
            "gesture_category": self.current_category,  # POSITIVE, NEGATIVE, NAVIGATION
            "target_note_or_chord": self.get_target_label(),
            "landmarks_left_hand": self.current_landmarks_left,
            "landmarks_right_hand": self.current_landmarks_right,
            "quality_scores": {
                "left_hand": quality_left,
                "right_hand": quality_right,
                "overall": overall_quality
            },
            "hands_detected": {
                "left_hand": len(self.current_landmarks_left) > 0,
                "right_hand": len(self.current_landmarks_right) > 0,
                "both_hands": len(self.current_landmarks_left) > 0 and len(self.current_landmarks_right) > 0
            },
            "sample_number": self.sample_count + 1
        }
        
        # ✅ INFORMACIÓN ESPECÍFICA POR CATEGORÍA
        if self.current_category == "POSITIVE":
            gesture_data["octave"] = self.current_octave
            gesture_data["positive_gesture_info"] = {
                "gesture_type": self.current_gesture_type,
                "note": self.target_var.get(),
                "note_with_octave": f"{self.target_var.get()}{self.current_octave}"
            }
            
        elif self.current_category == "NEGATIVE":
            gesture_data["negative_gesture_info"] = {
                "gesture_type": self.target_var.get(),
                "description": self.negative_gestures[self.target_var.get()]
            }
            
        elif self.current_category == "NAVIGATION":
            gesture_data["navigation_gesture_info"] = {
                "direction": self.target_var.get(),
                "description": self.navigation_gestures[self.target_var.get()]
            }
        
        # Guardar archivo
        filename = self.generate_filename()
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(gesture_data, f, indent=2, ensure_ascii=False)
            
        # Actualizar contadores
        self.sample_count += 1
        self.sample_label.config(text=f"Muestras: {self.sample_count}/{self.target_samples}")
        self.progress['value'] = (self.sample_count / self.target_samples) * 100
        
        # Mensaje de confirmación
        target_name = self.get_target_label()
        
        if self.sample_count >= self.target_samples:
            success_msg = f"🎉 ¡COMPLETADO!\n\n{self.target_samples} muestras capturadas para {target_name}\n\nCalidad promedio: {overall_quality:.1f}%"
            messagebox.showinfo("¡Objetivo Completado!", success_msg)
            self.sample_count = 0
            self.progress['value'] = 0
        else:
            remaining = self.target_samples - self.sample_count
            capture_msg = f"✅ ¡CAPTURADO!\n\nMuestra #{self.sample_count} de {target_name}\nCalidad: {overall_quality:.1f}%\n\nQuedan {remaining} muestras"
            self.show_capture_confirmation(capture_msg)
            
    def get_target_label(self):
        """Obtener etiqueta objetivo según categoría"""
        if self.current_category == "POSITIVE":
            return f"{self.target_var.get()}{self.current_octave}"
        else:
            return self.target_var.get()
            
    def show_capture_confirmation(self, message):
        """Mostrar confirmación de captura no bloqueante"""
        def show_temp_window():
            temp_window = tk.Toplevel(self.root)
            temp_window.title("Capturado")
            temp_window.geometry("300x150")
            temp_window.resizable(False, False)
            temp_window.transient(self.root)
            temp_window.grab_set()
            
            msg_label = ttk.Label(temp_window, text=message, justify=tk.CENTER, font=("Arial", 10))
            msg_label.pack(expand=True, pady=20)
            
            ok_btn = ttk.Button(temp_window, text="✅ Continuar", command=temp_window.destroy)
            ok_btn.pack(pady=10)
            
            temp_window.after(2000, temp_window.destroy)
            
        self.root.after(0, show_temp_window)
        
    def generate_filename(self):
        """Generar nombre de archivo único"""
        category = self.current_category.lower()
        target = self.target_var.get().replace("#", "sharp")
        sample_num = self.sample_count + 1
        
        if self.current_category == "POSITIVE":
            octave = self.current_octave
            gesture_type = self.current_gesture_type
            filename = f"{category}_{target}{octave}_{gesture_type}_sample_{sample_num:03d}.json"
        else:
            filename = f"{category}_{target}_sample_{sample_num:03d}.json"
            
        return filename
        
    def stop_camera(self):
        """Detener cámara"""
        self.capturing = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        
        self.status_label.config(text="Cámara detenida", foreground="red")
        self.start_camera_btn.config(state="normal")
        self.capture_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        
    def run(self):
        """Ejecutar aplicación"""
        self.root.mainloop()
        self.stop_camera()

if __name__ == "__main__":
    # Verificar dependencias
    try:
        import cv2
        import mediapipe
    except ImportError as e:
        print("❌ Faltan dependencias. Instala con:")
        print("pip install opencv-python mediapipe numpy")
        exit(1)
        
    print("🎹 CAPTURADOR DE GESTOS - 3 CATEGORÍAS")
    print("=" * 50)
    print("📊 CATEGORÍAS:")
    print("   🎵 POSITIVE: Notas y acordes (120 muestras c/u)")
    print("   ❌ NEGATIVE: Gestos que NO deben tocar (120 muestras c/u)")
    print("   🧭 NAVIGATION: Gestos de navegación (120 muestras c/u)")
    print("=" * 50)
        
    # Ejecutar aplicación
    app = PianoCaptureApp()
    app.run()