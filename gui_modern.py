import customtkinter as ctk
from tkinter import Canvas, messagebox
import threading
import time
from datetime import datetime
from typing import Dict, List
import math

from traffic_system import Direccion, ColorSemaforo, TipoVehiculo, Vehiculo
from controlador_threading import ControladorThreading
from controlador_multiprocessing import ControladorMultiprocessing
from simulador import GeneradorVehiculos


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VehiculoBase:
    """Clase base para vehículos animados"""
    def __init__(self, vehiculo: Vehiculo, canvas_id: int, x: float, y: float):
        self.vehiculo = vehiculo
        self.canvas_id = canvas_id
        self.x = x
        self.y = y
        self.velocidad_base = 3.0
        self.en_movimiento = False
        self.target_x = x
        self.target_y = y
    
    def actualizar_posicion(self):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distancia = math.sqrt(dx**2 + dy**2)
        
        if distancia < self.velocidad_base:
            self.x = self.target_x
            self.y = self.target_y
            return True
        
        velocidad = self.get_velocidad()
        self.x += (dx / distancia) * velocidad
        self.y += (dy / distancia) * velocidad
        return False
    
    def get_velocidad(self):
        return self.velocidad_base


class Auto(VehiculoBase):
    def __init__(self, vehiculo: Vehiculo, canvas_id: int, x: float, y: float):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 3.0
        self.emoji = '🚗'
        self.color = '#3b82f6'


class Moto(VehiculoBase):
    def __init__(self, vehiculo: Vehiculo, canvas_id: int, x: float, y: float):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 4.0
        self.emoji = '🏍️'
        self.color = '#fbbf24'


class Camion(VehiculoBase):
    def __init__(self, vehiculo: Vehiculo, canvas_id: int, x: float, y: float):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 2.0
        self.emoji = '🚚'
        self.color = '#fb923c'


class Ambulancia(VehiculoBase):
    def __init__(self, vehiculo: Vehiculo, canvas_id: int, x: float, y: float):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 5.0
        self.emoji = '🚑'
        self.color = '#ef4444'
    
    def get_velocidad(self):
        return self.velocidad_base * 1.5


class Policia(VehiculoBase):
    def __init__(self, vehiculo: Vehiculo, canvas_id: int, x: float, y: float):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 5.0
        self.emoji = '🚓'
        self.color = '#3b82f6'
    
    def get_velocidad(self):
        return self.velocidad_base * 1.5


class Bombero(VehiculoBase):
    def __init__(self, vehiculo: Vehiculo, canvas_id: int, x: float, y: float):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 5.0
        self.emoji = '🚒'
        self.color = '#dc2626'
    
    def get_velocidad(self):
        return self.velocidad_base * 1.5


def crear_vehiculo_animado(vehiculo: Vehiculo, canvas_id: int, x: float, y: float) -> VehiculoBase:
    """Factory para crear vehículo del tipo correcto"""
    tipos_vehiculos = {
        TipoVehiculo.AUTO: Auto,
        TipoVehiculo.MOTO: Moto,
        TipoVehiculo.CAMION: Camion,
        TipoVehiculo.AMBULANCIA: Ambulancia,
        TipoVehiculo.POLICIA: Policia,
        TipoVehiculo.BOMBERO: Bombero
    }
    clase = tipos_vehiculos.get(vehiculo.tipo, Auto)
    return clase(vehiculo, canvas_id, x, y)


class ModernTrafficGUI:
    """Interfaz gráfica moderna con CustomTkinter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🚦 Sistema de Control de Tráfico")
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.state('zoomed')
        
        self.controlador = None
        self.generador = GeneradorVehiculos()
        self.modo_seleccionado = None
        self.simulacion_activa = False
        
        self.vehiculos_animados: Dict[Direccion, List[VehiculoBase]] = {d: [] for d in Direccion}
        
        self.crear_interfaz()
        self.imprimir_inicio_consola()
    
    def imprimir_inicio_consola(self):
        print("\n" + "="*80)
        print("🚦 SISTEMA DE CONTROL DE TRÁFICO - INTERFAZ MODERNA")
        print("="*80)
        print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎨 Interfaz: CustomTkinter (Moderna)")
        print("="*80 + "\n")
    
    def crear_interfaz(self):
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="🚦 SISTEMA DE CONTROL DE TRÁFICO",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        self.crear_panel_control(main_frame)
        self.crear_canvas_simulacion(main_frame)
        self.crear_panel_estadisticas(main_frame)
    
    def crear_panel_control(self, parent):
        control_frame = ctk.CTkFrame(parent, corner_radius=15)
        control_frame.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(control_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        # Modo
        modo_frame = ctk.CTkFrame(inner, fg_color="transparent")
        modo_frame.grid(row=0, column=0, padx=10, sticky="w")
        
        ctk.CTkLabel(
            modo_frame,
            text="Modo de Paralelismo:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.modo_var = ctk.StringVar(value="threading")
        
        ctk.CTkRadioButton(
            modo_frame,
            text="🧵 Threading (Hilos)",
            variable=self.modo_var,
            value="threading",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", pady=2)
        
        ctk.CTkRadioButton(
            modo_frame,
            text="⚙️ Multiprocessing (Procesos)",
            variable=self.modo_var,
            value="multiprocessing",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", pady=2)
        
        # Configuración
        config_frame = ctk.CTkFrame(inner, fg_color="transparent")
        config_frame.grid(row=0, column=1, padx=30, sticky="w")
        
        ctk.CTkLabel(
            config_frame,
            text="Intervalo de Vehículos:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        interval_inner = ctk.CTkFrame(config_frame, fg_color="transparent")
        interval_inner.pack(anchor="w")
        
        self.intervalo_var = ctk.DoubleVar(value=1.5)
        self.intervalo_slider = ctk.CTkSlider(
            interval_inner,
            from_=0.5,
            to=5.0,
            number_of_steps=9,
            variable=self.intervalo_var,
            width=200
        )
        self.intervalo_slider.pack(side="left", padx=(0, 10))
        
        self.intervalo_label = ctk.CTkLabel(
            interval_inner,
            text="1.5s",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=50
        )
        self.intervalo_label.pack(side="left")
        
        self.intervalo_slider.configure(command=self.actualizar_intervalo_label)
        
        # Botones de control
        botones_frame = ctk.CTkFrame(inner, fg_color="transparent")
        botones_frame.grid(row=0, column=2, padx=30, sticky="w")
        
        ctk.CTkLabel(
            botones_frame,
            text="Control del Sistema:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        botones_inner = ctk.CTkFrame(botones_frame, fg_color="transparent")
        botones_inner.pack(anchor="w")
        
        self.btn_iniciar = ctk.CTkButton(
            botones_inner,
            text="▶️ Iniciar Sistema",
            command=self.iniciar_sistema,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669"
        )
        self.btn_iniciar.pack(side="left", padx=5)
        
        self.btn_detener = ctk.CTkButton(
            botones_inner,
            text="⏹️ Detener Sistema",
            command=self.detener_sistema,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            state="disabled"
        )
        self.btn_detener.pack(side="left", padx=5)
        
        # Estado
        estado_frame = ctk.CTkFrame(inner, fg_color="transparent")
        estado_frame.grid(row=0, column=3, padx=30, sticky="w")
        
        ctk.CTkLabel(
            estado_frame,
            text="Estado:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.lbl_estado = ctk.CTkLabel(
            estado_frame,
            text="⭕ Sistema Detenido",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ef4444"
        )
        self.lbl_estado.pack(anchor="w")
        
        # Agregar vehículos
        vehiculos_frame = ctk.CTkFrame(inner, fg_color="transparent")
        vehiculos_frame.grid(row=0, column=4, padx=30, sticky="w")
        
        ctk.CTkLabel(
            vehiculos_frame,
            text="Agregar Vehículos:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        vehiculos_inner = ctk.CTkFrame(vehiculos_frame, fg_color="transparent")
        vehiculos_inner.pack(anchor="w")
        
        vehiculos = [
            ("🚗", "Auto", "#3b82f6"),
            ("🏍️", "Moto", "#fbbf24"),
            ("🚚", "Camión", "#fb923c"),
            ("🚑", "Ambulancia", "#ef4444"),
            ("🚓", "Policía", "#3b82f6"),
            ("🚒", "Bombero", "#dc2626")
        ]
        
        for emoji, tipo, color in vehiculos:
            btn = ctk.CTkButton(
                vehiculos_inner,
                text=emoji,
                command=lambda t=tipo: self.agregar_vehiculo_manual(t),
                width=45,
                height=45,
                font=ctk.CTkFont(size=20),
                fg_color=color,
                hover_color=self.darker_color(color)
            )
            btn.pack(side="left", padx=2)
    
    def actualizar_intervalo_label(self, value):
        self.intervalo_label.configure(text=f"{value:.1f}s")
    
    def darker_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = max(0, r-30), max(0, g-30), max(0, b-30)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def crear_canvas_simulacion(self, parent):
        canvas_frame = ctk.CTkFrame(parent, corner_radius=15)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        legend_frame = ctk.CTkFrame(canvas_frame, fg_color="transparent")
        legend_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            legend_frame,
            text="🚗 Auto (3.0x)  🏍️ Moto (4.0x)  🚚 Camión (2.0x)  |  🚑 Ambulancia (7.5x)  🚓 Policía (7.5x)  🚒 Bombero (7.5x)",
            font=ctk.CTkFont(size=13)
        ).pack()
        
        self.canvas = Canvas(
            canvas_frame,
            bg='#1e293b',
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.canvas.bind('<Configure>', self.dibujar_interseccion)
    
    def crear_panel_estadisticas(self, parent):
        stats_frame = ctk.CTkFrame(parent, corner_radius=15)
        stats_frame.pack(fill="x")
        
        inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            inner,
            text="📊 Estadísticas en Tiempo Real",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=4, pady=(0, 15))
        
        self.stats_labels = {}
        
        direcciones_info = [
            (Direccion.NORTE, "📍", 0),
            (Direccion.SUR, "📍", 1),
            (Direccion.ESTE, "📍", 2),
            (Direccion.OESTE, "📍", 3)
        ]
        
        for direccion, emoji, col in direcciones_info:
            dir_frame = ctk.CTkFrame(inner, corner_radius=10)
            dir_frame.grid(row=1, column=col, padx=10, sticky="nsew")
            inner.columnconfigure(col, weight=1)
            
            ctk.CTkLabel(
                dir_frame,
                text=f"{emoji} {direccion.value.upper()}",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=(10, 5))
            
            stats_label = ctk.CTkLabel(
                dir_frame,
                text="Esperando: 0\nPasados: 0",
                font=ctk.CTkFont(size=14),
                justify="center"
            )
            stats_label.pack(pady=(5, 10))
            
            self.stats_labels[direccion] = stats_label
    
    def dibujar_interseccion(self, event=None):
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width < 100 or height < 100:
            return
        
        self.center_x = width // 2
        self.center_y = height // 2
        self.road_width = 120
        self.intersection_size = 180
        
        self.canvas.create_rectangle(
            self.center_x - self.road_width // 2, 0,
            self.center_x + self.road_width // 2, height,
            fill='#374151', outline='', width=0
        )
        
        self.canvas.create_rectangle(
            0, self.center_y - self.road_width // 2,
            width, self.center_y + self.road_width // 2,
            fill='#374151', outline='', width=0
        )
        
        self.canvas.create_line(
            self.center_x, 0, self.center_x, height,
            fill='#fbbf24', width=4, dash=(20, 10)
        )
        self.canvas.create_line(
            0, self.center_y, width, self.center_y,
            fill='#fbbf24', width=4, dash=(20, 10)
        )
        
        self.canvas.create_rectangle(
            self.center_x - self.intersection_size // 2,
            self.center_y - self.intersection_size // 2,
            self.center_x + self.intersection_size // 2,
            self.center_y + self.intersection_size // 2,
            fill='#475569', outline='', width=0
        )
        
        self.dibujar_semaforos()
        self.definir_posiciones()
    
    def definir_posiciones(self):
        offset_espera = self.intersection_size // 2 + 60
        
        self.posiciones_espera = {
            Direccion.NORTE: {
                'espera': (self.center_x + 20, self.center_y - offset_espera),
                'salida': (self.center_x + 20, self.canvas.winfo_height() - 50),
                'dx': 0, 'dy': -40
            },
            Direccion.SUR: {
                'espera': (self.center_x - 20, self.center_y + offset_espera),
                'salida': (self.center_x - 20, 50),
                'dx': 0, 'dy': 40
            },
            Direccion.ESTE: {
                'espera': (self.center_x + offset_espera, self.center_y - 20),
                'salida': (50, self.center_y - 20),
                'dx': 40, 'dy': 0
            },
            Direccion.OESTE: {
                'espera': (self.center_x - offset_espera, self.center_y + 20),
                'salida': (self.canvas.winfo_width() - 50, self.center_y + 20),
                'dx': -40, 'dy': 0
            }
        }
    
    def dibujar_semaforos(self):
        offset = self.intersection_size // 2 + 35
        size = 35
        
        self.semaforos_canvas = {
            Direccion.NORTE: self.dibujar_semaforo(
                self.center_x - 55, self.center_y - offset - 100, size, "NORTE"
            ),
            Direccion.SUR: self.dibujar_semaforo(
                self.center_x + 55, self.center_y + offset + 55, size, "SUR"
            ),
            Direccion.ESTE: self.dibujar_semaforo(
                self.center_x + offset + 55, self.center_y + 55, size, "ESTE"
            ),
            Direccion.OESTE: self.dibujar_semaforo(
                self.center_x - offset - 100, self.center_y - 55, size, "OESTE"
            )
        }
    
    def dibujar_semaforo(self, x, y, size, label):
        self.canvas.create_rectangle(
            x+2, y+2, x + size * 1.2 + 2, y + size * 3.5 + 2,
            fill='#000000', outline='', width=0
        )
        
        self.canvas.create_rectangle(
            x, y, x + size * 1.2, y + size * 3.5,
            fill='#1e293b', outline='#64748b', width=3
        )
        
        luces = {
            'rojo': self.canvas.create_oval(
                x + size * 0.1, y + size * 0.2,
                x + size * 1.1, y + size * 1.0,
                fill='#450a0a', outline='#7f1d1d', width=2
            ),
            'amarillo': self.canvas.create_oval(
                x + size * 0.1, y + size * 1.25,
                x + size * 1.1, y + size * 2.05,
                fill='#451a03', outline='#78350f', width=2
            ),
            'verde': self.canvas.create_oval(
                x + size * 0.1, y + size * 2.5,
                x + size * 1.1, y + size * 3.3,
                fill='#052e16', outline='#14532d', width=2
            )
        }
        
        self.canvas.create_text(
            x + size * 0.6, y + size * 3.9,
            text=label,
            fill='#f1f5f9',
            font=("Arial", 11, "bold")
        )
        
        return luces
    
    def iniciar_sistema(self):
        modo = self.modo_var.get()
        
        print(f"\n{'='*80}")
        print(f"🚀 INICIANDO - Modo: {modo.upper()}")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        if modo == "threading":
            print("🧵 THREADING")
            self.controlador = ControladorThreading()
            self.modo_seleccionado = "Threading"
        else:
            print("⚙️ MULTIPROCESSING")
            self.controlador = ControladorMultiprocessing()
            self.modo_seleccionado = "Multiprocessing"
        
        print(f"{'='*80}\n")
        
        self.controlador.iniciar()
        self.simulacion_activa = True
        
        self.btn_iniciar.configure(state="disabled")
        self.btn_detener.configure(state="normal")
        self.lbl_estado.configure(text="✅ Sistema Activo", text_color="#10b981")
        
        threading.Thread(target=self.loop_actualizacion, daemon=True).start()
        threading.Thread(target=self.generar_vehiculos_auto, daemon=True).start()
        
        self.animar_vehiculos()
    
    def detener_sistema(self):
        if self.controlador:
            print(f"\n{'='*80}")
            print(f"🛑 DETENIENDO - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*80}\n")
            
            self.simulacion_activa = False
            self.controlador.detener()
            
            self.btn_iniciar.configure(state="normal")
            self.btn_detener.configure(state="disabled")
            self.lbl_estado.configure(text="⭕ Sistema Detenido", text_color="#ef4444")
            
            for direccion in Direccion:
                for v in self.vehiculos_animados[direccion]:
                    self.canvas.delete(v.canvas_id)
                self.vehiculos_animados[direccion].clear()
            
            self.controlador = None
    
    def loop_actualizacion(self):
        while self.simulacion_activa and self.controlador:
            try:
                self.actualizar_semaforos()
                self.actualizar_estadisticas()
                self.sincronizar_vehiculos()
                time.sleep(0.15)
            except:
                break
    
    def actualizar_semaforos(self):
        if not self.controlador:
            return
        
        try:
            for direccion, luces in self.semaforos_canvas.items():
                if hasattr(self.controlador, 'calles'):
                    color = self.controlador.calles[direccion].semaforo.color
                elif hasattr(self.controlador, 'estados_semaforos'):
                    color = ColorSemaforo(self.controlador.estados_semaforos[direccion.value]['color'])
                else:
                    continue
                
                self.canvas.itemconfig(luces['rojo'], fill='#450a0a')
                self.canvas.itemconfig(luces['amarillo'], fill='#451a03')
                self.canvas.itemconfig(luces['verde'], fill='#052e16')
                
                if color == ColorSemaforo.ROJO:
                    self.canvas.itemconfig(luces['rojo'], fill='#ef4444')
                elif color == ColorSemaforo.AMARILLO:
                    self.canvas.itemconfig(luces['amarillo'], fill='#fbbf24')
                elif color == ColorSemaforo.VERDE:
                    self.canvas.itemconfig(luces['verde'], fill='#10b981')
        except:
            pass
    
    def actualizar_estadisticas(self):
        if not self.controlador:
            return
        
        try:
            stats = self.controlador.obtener_estadisticas()
            
            for direccion, label in self.stats_labels.items():
                if self.modo_seleccionado == "Threading":
                    data = stats[direccion.value]
                else:
                    data = stats.get(direccion.value, {'esperando': 0, 'pasados': 0})
                
                label.configure(text=f"Esperando: {data['esperando']}\nPasados: {data['pasados']}")
        except:
            pass
    
    def sincronizar_vehiculos(self):
        if not self.controlador:
            return
        
        try:
            for direccion in Direccion:
                cola_vehiculos = []
                
                if hasattr(self.controlador, 'calles'):
                    cola_vehiculos = self.controlador.calles[direccion].cola.vehiculos[:5]
                elif hasattr(self.controlador, 'colas_vehiculos'):
                    cola_list = list(self.controlador.colas_vehiculos[direccion.value])[:5]
                    for v_data in cola_list:
                        cola_vehiculos.append(Vehiculo(
                            id=v_data['id'],
                            tipo=TipoVehiculo[v_data['tipo']],
                            direccion=direccion,
                            tiempo_llegada=v_data['tiempo_llegada']
                        ))
                
                ids_cola = [v.id for v in cola_vehiculos]
                for v_anim in self.vehiculos_animados[direccion][:]:
                    if v_anim.vehiculo.id not in ids_cola:
                        self.canvas.delete(v_anim.canvas_id)
                        self.vehiculos_animados[direccion].remove(v_anim)
                
                ids_canvas = [v.vehiculo.id for v in self.vehiculos_animados[direccion]]
                
                for i, vehiculo in enumerate(cola_vehiculos):
                    if vehiculo.id not in ids_canvas and i < 5:
                        pos = self.posiciones_espera[direccion]
                        x = pos['espera'][0] + pos['dx'] * i
                        y = pos['espera'][1] + pos['dy'] * i
                        
                        v_obj = crear_vehiculo_animado(vehiculo, None, x, y)
                        
                        canvas_id = self.canvas.create_text(
                            x, y,
                            text=v_obj.emoji,
                            font=("Arial", 26),
                            fill=v_obj.color,
                            tags="vehiculo"
                        )
                        
                        v_obj.canvas_id = canvas_id
                        self.vehiculos_animados[direccion].append(v_obj)
        except:
            pass
    
    def animar_vehiculos(self):
        if not self.simulacion_activa:
            return
        
        for direccion in Direccion:
            for v_anim in self.vehiculos_animados[direccion][:]:
                if v_anim.en_movimiento:
                    completado = v_anim.actualizar_posicion()
                    self.canvas.coords(v_anim.canvas_id, v_anim.x, v_anim.y)
                    
                    if completado:
                        self.canvas.delete(v_anim.canvas_id)
                        self.vehiculos_animados[direccion].remove(v_anim)
                else:
                    puede_avanzar = False
                    
                    if hasattr(self.controlador, 'calles'):
                        semaforo = self.controlador.calles[direccion].semaforo
                        puede_avanzar = semaforo.puede_avanzar() or v_anim.vehiculo.es_emergencia
                    elif hasattr(self.controlador, 'estados_semaforos'):
                        estado = self.controlador.estados_semaforos[direccion.value]
                        puede_avanzar = (estado['color'] == ColorSemaforo.VERDE.value and 
                                       not estado['bloqueado']) or v_anim.vehiculo.es_emergencia
                    
                    if puede_avanzar and self.vehiculos_animados[direccion].index(v_anim) == 0:
                        pos = self.posiciones_espera[direccion]
                        v_anim.target_x = pos['salida'][0]
                        v_anim.target_y = pos['salida'][1]
                        v_anim.en_movimiento = True
        
        self.root.after(25, self.animar_vehiculos)
    
    def generar_vehiculos_auto(self):
        intervalo = self.intervalo_var.get()
        print(f"🚗 Generación automática (intervalo: {intervalo}s)\n")
        
        contador = 0
        while self.simulacion_activa and self.controlador:
            contador += 1
            
            if contador % 10 == 0:
                vehiculo = self.generador.generar_emergencia()
                print(f"🚨 {vehiculo}")
            else:
                vehiculo = self.generador.generar_vehiculo()
            
            self.controlador.agregar_vehiculo_seguro(vehiculo)
            time.sleep(intervalo)
    
    def agregar_vehiculo_manual(self, tipo_str):
        if not self.controlador:
            messagebox.showwarning("Sistema Detenido", "Inicia el sistema primero")
            return
        
        tipos = {
            "Auto": TipoVehiculo.AUTO,
            "Moto": TipoVehiculo.MOTO,
            "Camión": TipoVehiculo.CAMION,
            "Ambulancia": TipoVehiculo.AMBULANCIA,
            "Policía": TipoVehiculo.POLICIA,
            "Bombero": TipoVehiculo.BOMBERO
        }
        
        vehiculo = self.generador.generar_vehiculo(tipo=tipos[tipo_str])
        self.controlador.agregar_vehiculo_seguro(vehiculo)
        print(f"➕ {vehiculo}")


def main():
    print("\n" + "="*80)
    print("🚦 SISTEMA DE CONTROL DE TRÁFICO - INTERFAZ MODERNA")
    print("="*80)
    print("🎨 CustomTkinter - Diseño Profesional")
    print("="*80 + "\n")
    
    root = ctk.CTk()
    app = ModernTrafficGUI(root)
    
    def on_closing():
        if app.controlador:
            if messagebox.askokcancel("Salir", "¿Cerrar el sistema?"):
                app.detener_sistema()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
