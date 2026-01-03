"""
GUI Sistema de Tráfico - Cuenca, Ecuador
Manzana: Pío Bravo, María Arizaga, Tarqui, Juan Montalvo
"""

import customtkinter as ctk
from tkinter import Canvas, messagebox
import threading
import time
from datetime import datetime
from typing import Dict, List
import math

from traffic_system_cuenca import CalleCuenca, ColorSemaforo, TipoVehiculo, Vehiculo
from controlador_threading_cuenca import ControladorThreadingCuenca
from controlador_multiprocessing_cuenca import ControladorMultiprocessingCuenca
from simulador_cuenca import GeneradorVehiculosCuenca


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VehiculoBase:
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
    def __init__(self, vehiculo, canvas_id, x, y):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 3.0
        self.emoji = '🚗'
        self.color = '#3b82f6'


class Moto(VehiculoBase):
    def __init__(self, vehiculo, canvas_id, x, y):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 4.0
        self.emoji = '🏍️'
        self.color = '#fbbf24'


class Bus(VehiculoBase):
    def __init__(self, vehiculo, canvas_id, x, y):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 2.5
        self.emoji = '🚌'
        self.color = '#f59e0b'


class Camion(VehiculoBase):
    def __init__(self, vehiculo, canvas_id, x, y):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 2.0
        self.emoji = '🚚'
        self.color = '#fb923c'


class Ambulancia(VehiculoBase):
    def __init__(self, vehiculo, canvas_id, x, y):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 5.0
        self.emoji = '🚑'
        self.color = '#ef4444'
    
    def get_velocidad(self):
        return self.velocidad_base * 1.5


class Policia(VehiculoBase):
    def __init__(self, vehiculo, canvas_id, x, y):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 5.0
        self.emoji = '🚓'
        self.color = '#3b82f6'
    
    def get_velocidad(self):
        return self.velocidad_base * 1.5


class Bombero(VehiculoBase):
    def __init__(self, vehiculo, canvas_id, x, y):
        super().__init__(vehiculo, canvas_id, x, y)
        self.velocidad_base = 5.0
        self.emoji = '🚒'
        self.color = '#dc2626'
    
    def get_velocidad(self):
        return self.velocidad_base * 1.5


def crear_vehiculo_animado(vehiculo: Vehiculo, canvas_id: int, x: float, y: float):
    tipos = {
        TipoVehiculo.AUTO: Auto,
        TipoVehiculo.MOTO: Moto,
        TipoVehiculo.BUS: Bus,
        TipoVehiculo.CAMION: Camion,
        TipoVehiculo.AMBULANCIA: Ambulancia,
        TipoVehiculo.POLICIA: Policia,
        TipoVehiculo.BOMBERO: Bombero
    }
    clase = tipos.get(vehiculo.tipo, Auto)
    return clase(vehiculo, canvas_id, x, y)


class TrafficGUICuenca:
    """GUI para el sistema de tráfico de Cuenca"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🚦 Sistema de Tráfico - Cuenca, Ecuador")
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.state('zoomed')
        
        self.controlador = None
        self.generador = GeneradorVehiculosCuenca()
        self.simulacion_activa = False
        
        self.vehiculos_animados: Dict[CalleCuenca, List] = {c: [] for c in CalleCuenca}
        
        self.crear_interfaz()
        self.imprimir_inicio()
    
    def imprimir_inicio(self):
        print("\n" + "="*80)
        print("🚦 SISTEMA DE TRÁFICO - CUENCA, ECUADOR")
        print("="*80)
        print(f"📍 Manzana: Pío Bravo - María Arizaga - Tarqui - Juan Montalvo")
        print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def crear_interfaz(self):
        # Contenedor con scroll
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True)
        
        canvas_scroll = Canvas(main_container, highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(main_container, orientation="vertical", command=canvas_scroll.yview)
        
        scrollable_frame = ctk.CTkFrame(canvas_scroll, fg_color="transparent")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        )
        
        canvas_scroll.create_window((0, 0), window=scrollable_frame, anchor="nw", width=self.root.winfo_screenwidth())
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        
        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            canvas_scroll.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel)
        
        main_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            main_frame,
            text="🚦 SISTEMA DE TRÁFICO - CUENCA, ECUADOR",
            font=ctk.CTkFont(size=32, weight="bold")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            main_frame,
            text="Manzana: Pío Bravo - María Arizaga - Tarqui - Juan Montalvo",
            font=ctk.CTkFont(size=16)
        ).pack(pady=(0, 20))
        
        self.crear_controles(main_frame)
        self.crear_canvas(main_frame)
        self.crear_estadisticas(main_frame)
    
    def crear_controles(self, parent):
        control_frame = ctk.CTkFrame(parent, corner_radius=15)
        control_frame.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(control_frame, fg_color="transparent")
        inner.pack(padx=20, pady=15)
        
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack()
        
        # Modo
        ctk.CTkLabel(
            row,
            text="Modo:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        self.modo_var = ctk.StringVar(value="threading")
        
        ctk.CTkRadioButton(
            row,
            text="🧵 Threading",
            variable=self.modo_var,
            value="threading",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=5)
        
        ctk.CTkRadioButton(
            row,
            text="⚙️ Multiprocessing",
            variable=self.modo_var,
            value="multiprocessing",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(5, 30))
        
        # Intervalo
        ctk.CTkLabel(
            row,
            text="Intervalo:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        self.intervalo_var = ctk.DoubleVar(value=1.5)
        self.intervalo_slider = ctk.CTkSlider(
            row,
            from_=0.5,
            to=5.0,
            number_of_steps=9,
            variable=self.intervalo_var,
            width=200
        )
        self.intervalo_slider.pack(side="left", padx=(0, 10))
        
        self.intervalo_label = ctk.CTkLabel(
            row,
            text="1.5s",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=50
        )
        self.intervalo_label.pack(side="left", padx=(0, 30))
        
        self.intervalo_slider.configure(command=lambda v: self.intervalo_label.configure(text=f"{v:.1f}s"))
        
        # Botones
        self.btn_iniciar = ctk.CTkButton(
            row,
            text="▶️ Iniciar",
            command=self.iniciar_sistema,
            width=150,
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669"
        )
        self.btn_iniciar.pack(side="left", padx=5)
        
        self.btn_detener = ctk.CTkButton(
            row,
            text="⏹️ Detener",
            command=self.detener_sistema,
            width=150,
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            state="disabled"
        )
        self.btn_detener.pack(side="left", padx=5)
        
        # Estado
        self.lbl_estado = ctk.CTkLabel(
            row,
            text="⭕ Detenido",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ef4444"
        )
        self.lbl_estado.pack(side="left", padx=30)
        
        # SEGUNDA FILA: Agregar vehículos (separada y visible)
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(15, 0))
        
        ctk.CTkLabel(
            row2,
            text="➕ Agregar Vehículos:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=(0, 20))
        
        vehiculos = [
            ("🚗", "Auto", "#3b82f6"),
            ("🏍️", "Moto", "#fbbf24"),
            ("🚌", "Bus", "#f59e0b"),
            ("🚚", "Camión", "#fb923c"),
            ("🚑", "Ambulancia", "#ef4444"),
            ("🚓", "Policía", "#3b82f6"),
            ("🚒", "Bombero", "#dc2626")
        ]
        
        for emoji, tipo, color in vehiculos:
            ctk.CTkButton(
                row2,
                text=emoji,
                command=lambda t=tipo: self.agregar_vehiculo_manual(t),
                width=60,
                height=60,
                font=ctk.CTkFont(size=24),
                fg_color=color,
                hover_color=self.darker_color(color),
                corner_radius=10
            ).pack(side="left", padx=5)
    
    def darker_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = max(0, r-30), max(0, g-30), max(0, b-30)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def crear_canvas(self, parent):
        canvas_frame = ctk.CTkFrame(parent, corner_radius=15)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        ctk.CTkLabel(
            canvas_frame,
            text="VISUALIZACIÓN DE LA MANZANA",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        self.canvas = Canvas(
            canvas_frame,
            bg='#1e293b',
            highlightthickness=0,
            height=700
        )
        self.canvas.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.canvas.bind('<Configure>', self.dibujar_manzana)
    
    def crear_estadisticas(self, parent):
        stats_frame = ctk.CTkFrame(parent, corner_radius=15)
        stats_frame.pack(fill="x")
        
        inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            inner,
            text="📊 Estadísticas por Calle",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=4, pady=(0, 10))
        
        self.stats_labels = {}
        
        calles_info = [
            (CalleCuenca.PIO_BRAVO, "📍", 0),
            (CalleCuenca.MARIA_ARIZAGA, "📍", 1),
            (CalleCuenca.TARQUI, "📍", 2),
            (CalleCuenca.JUAN_MONTALVO, "📍", 3)
        ]
        
        for calle, emoji, col in calles_info:
            dir_frame = ctk.CTkFrame(inner, corner_radius=10)
            dir_frame.grid(row=1, column=col, padx=8, sticky="nsew")
            inner.columnconfigure(col, weight=1)
            
            ctk.CTkLabel(
                dir_frame,
                text=f"{emoji} {calle.value}",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(8, 3))
            
            stats_label = ctk.CTkLabel(
                dir_frame,
                text="Esperando: 0\nPasados: 0",
                font=ctk.CTkFont(size=13),
                justify="center"
            )
            stats_label.pack(pady=(3, 8))
            
            self.stats_labels[calle] = stats_label
    
    def dibujar_manzana(self, event=None):
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width < 100 or height < 100:
            return
        
        self.center_x = width // 2
        self.center_y = height // 2
        
        # Manzana central (edificios/casas)
        manzana_width = 400
        manzana_height = 300
        
        self.canvas.create_rectangle(
            self.center_x - manzana_width // 2,
            self.center_y - manzana_height // 2,
            self.center_x + manzana_width // 2,
            self.center_y + manzana_height // 2,
            fill='#475569',
            outline='#cbd5e1',
            width=3
        )
        
        # Calles alrededor
        road_width = 100
        
        # Pío Bravo (abajo)
        self.canvas.create_rectangle(
            50, self.center_y + manzana_height // 2,
            width - 50, self.center_y + manzana_height // 2 + road_width,
            fill='#374151', outline=''
        )
        
        # María Arizaga (arriba)
        self.canvas.create_rectangle(
            50, self.center_y - manzana_height // 2 - road_width,
            width - 50, self.center_y - manzana_height // 2,
            fill='#374151', outline=''
        )
        
        # Tarqui (derecha)
        self.canvas.create_rectangle(
            self.center_x + manzana_width // 2,
            50,
            self.center_x + manzana_width // 2 + road_width,
            height - 50,
            fill='#374151', outline=''
        )
        
        # Juan Montalvo (izquierda)
        self.canvas.create_rectangle(
            self.center_x - manzana_width // 2 - road_width,
            50,
            self.center_x - manzana_width // 2,
            height - 50,
            fill='#374151', outline=''
        )
        
        self.dibujar_semaforos()
        self.definir_posiciones()
    
    def dibujar_semaforos(self):
        size = 35
        manzana_width = 400
        manzana_height = 300
        road_width = 100
        
        # Semáforos en las ESQUINAS EXTERIORES según tu boceto
        # Cada semáforo está en la esquina de SU calle, fuera de la manzana
        
        self.semaforos_canvas = {
            # Pío Bravo (ABAJO): Esquina INFERIOR DERECHA de su calle
            CalleCuenca.PIO_BRAVO: self.dibujar_semaforo(
                self.center_x + manzana_width // 2 + 15,
                self.center_y + manzana_height // 2 + road_width - size * 3.5 - 15,
                size, "Pío Bravo"
            ),
            
            # María Arizaga (ARRIBA): Esquina SUPERIOR IZQUIERDA de su calle
            CalleCuenca.MARIA_ARIZAGA: self.dibujar_semaforo(
                self.center_x - manzana_width // 2 - road_width + 15,
                self.center_y - manzana_height // 2 - road_width + 15,
                size, "M. Auxiliadora"
            ),
            
            # Tarqui (DERECHA): Esquina SUPERIOR DERECHA de su calle
            CalleCuenca.TARQUI: self.dibujar_semaforo(
                self.center_x + manzana_width // 2 + road_width - size * 1.2 - 15,
                self.center_y - manzana_height // 2 - road_width + 15,
                size, "Tarqui"
            ),
            
            # Juan Montalvo (IZQUIERDA): Esquina INFERIOR IZQUIERDA de su calle
            CalleCuenca.JUAN_MONTALVO: self.dibujar_semaforo(
                self.center_x - manzana_width // 2 - road_width + 15,
                self.center_y + manzana_height // 2 + road_width - size * 3.5 - 15,
                size, "J. Montalvo"
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
            font=("Arial", 10, "bold")
        )
        
        return luces
    
    def definir_posiciones(self):
        # Los vehículos:
        # 1. Esperan ANTES del semáforo (espera)
        # 2. Cuando verde, PASAN el semáforo
        # 3. Recorren TODA la calle hasta el borde (salida)
        # 4. Desaparecen al llegar al borde final
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        manzana_width = 400
        manzana_height = 300
        road_width = 100
        
        self.posiciones_espera = {
            # Pío Bravo (ABAJO): Esperan a la IZQUIERDA, salen por la DERECHA
            # Dirección: IZQUIERDA → DERECHA
            CalleCuenca.PIO_BRAVO: {
                'espera': (self.center_x - manzana_width // 2 - road_width + 80, self.center_y + 220),
                'salida': (canvas_width - 30, self.center_y + 220),
                'dx': -45, 'dy': 0
            },
            
            # María Arizaga (ARRIBA): Esperan a la DERECHA, salen por la IZQUIERDA
            # Dirección: DERECHA → IZQUIERDA
            CalleCuenca.MARIA_ARIZAGA: {
                'espera': (self.center_x + manzana_width // 2 + road_width - 80, self.center_y - 220),
                'salida': (30, self.center_y - 220),
                'dx': 45, 'dy': 0
            },
            
            # Tarqui (DERECHA): Esperan ABAJO, salen por ARRIBA
            # Dirección: ABAJO → ARRIBA
            CalleCuenca.TARQUI: {
                'espera': (self.center_x + 240, self.center_y + manzana_height // 2 + road_width - 80),
                'salida': (self.center_x + 240, 30),
                'dx': 0, 'dy': 45
            },
            
            # Juan Montalvo (IZQUIERDA): Esperan ARRIBA, salen por ABAJO
            # Dirección: ARRIBA → ABAJO
            CalleCuenca.JUAN_MONTALVO: {
                'espera': (self.center_x - 240, self.center_y - manzana_height // 2 - road_width + 80),
                'salida': (self.center_x - 240, canvas_height - 30),
                'dx': 0, 'dy': -45
            }
        }
    
    def iniciar_sistema(self):
        modo = self.modo_var.get()
        
        print(f"\n{'='*80}")
        print(f"🚀 INICIANDO SISTEMA - {modo.upper()}")
        print(f"{'='*80}\n")
        
        if modo == "threading":
            self.controlador = ControladorThreadingCuenca()
            self.modo_seleccionado = "Threading"
        else:
            self.controlador = ControladorMultiprocessingCuenca()
            self.modo_seleccionado = "Multiprocessing"
        
        self.controlador.iniciar()
        self.simulacion_activa = True
        
        self.btn_iniciar.configure(state="disabled")
        self.btn_detener.configure(state="normal")
        self.lbl_estado.configure(text="✅ Activo", text_color="#10b981")
        
        threading.Thread(target=self.loop_actualizacion, daemon=True).start()
        threading.Thread(target=self.generar_vehiculos_auto, daemon=True).start()
        
        self.animar_vehiculos()
    
    def detener_sistema(self):
        if self.controlador:
            self.simulacion_activa = False
            self.controlador.detener()
            
            self.btn_iniciar.configure(state="normal")
            self.btn_detener.configure(state="disabled")
            self.lbl_estado.configure(text="⭕ Detenido", text_color="#ef4444")
            
            for calle in CalleCuenca:
                for v in self.vehiculos_animados[calle]:
                    self.canvas.delete(v.canvas_id)
                self.vehiculos_animados[calle].clear()
            
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
            if self.modo_seleccionado == "Threading":
                for calle, luces in self.semaforos_canvas.items():
                    color = self.controlador.semaforos[calle].color
                    
                    self.canvas.itemconfig(luces['rojo'], fill='#450a0a')
                    self.canvas.itemconfig(luces['amarillo'], fill='#451a03')
                    self.canvas.itemconfig(luces['verde'], fill='#052e16')
                    
                    if color == ColorSemaforo.ROJO:
                        self.canvas.itemconfig(luces['rojo'], fill='#ef4444')
                    elif color == ColorSemaforo.AMARILLO:
                        self.canvas.itemconfig(luces['amarillo'], fill='#fbbf24')
                    elif color == ColorSemaforo.VERDE:
                        self.canvas.itemconfig(luces['verde'], fill='#10b981')
            else:
                stats = self.controlador.obtener_estadisticas()
                for calle, luces in self.semaforos_canvas.items():
                    color_str = stats[calle.value]['color']
                    color = ColorSemaforo(color_str)
                    
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
            
            for calle, label in self.stats_labels.items():
                data = stats[calle.value]
                label.configure(text=f"Esperando: {data['esperando']}\nPasados: {data['pasados']}")
        except:
            pass
    
    def sincronizar_vehiculos(self):
        if not self.controlador:
            return
        
        try:
            for calle in CalleCuenca:
                cola_vehiculos = []
                
                if self.modo_seleccionado == "Threading":
                    semaforo = self.controlador.semaforos[calle]
                    with semaforo.lock:
                        cola_vehiculos = semaforo.cola_vehiculos.vehiculos[:8]
                else:
                    # En multiprocessing no mostramos vehículos individuales
                    continue
                
                ids_cola = [v.id for v in cola_vehiculos]
                for v_anim in self.vehiculos_animados[calle][:]:
                    if v_anim.vehiculo.id not in ids_cola:
                        self.canvas.delete(v_anim.canvas_id)
                        self.vehiculos_animados[calle].remove(v_anim)
                
                ids_canvas = [v.vehiculo.id for v in self.vehiculos_animados[calle]]
                
                for i, vehiculo in enumerate(cola_vehiculos):
                    if vehiculo.id not in ids_canvas:
                        pos = self.posiciones_espera[calle]
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
                        self.vehiculos_animados[calle].append(v_obj)
        except:
            pass
    
    def animar_vehiculos(self):
        if not self.simulacion_activa:
            return
        
        for calle in CalleCuenca:
            for v_anim in self.vehiculos_animados[calle][:]:
                if v_anim.en_movimiento:
                    completado = v_anim.actualizar_posicion()
                    self.canvas.coords(v_anim.canvas_id, v_anim.x, v_anim.y)
                    
                    if completado:
                        self.canvas.delete(v_anim.canvas_id)
                        self.vehiculos_animados[calle].remove(v_anim)
                else:
                    # PRIORIDAD: Las emergencias SIEMPRE pasan
                    if v_anim.vehiculo.es_emergencia:
                        # Si es emergencia, pasa INMEDIATAMENTE (sin importar posición o color)
                        if self.vehiculos_animados[calle].index(v_anim) == 0:
                            pos = self.posiciones_espera[calle]
                            v_anim.target_x = pos['salida'][0]
                            v_anim.target_y = pos['salida'][1]
                            v_anim.en_movimiento = True
                    else:
                        # Vehículos normales: solo pasan si están primero Y semáforo verde
                        if self.modo_seleccionado == "Threading":
                            semaforo = self.controlador.semaforos[calle]
                            puede_avanzar = semaforo.color == ColorSemaforo.VERDE
                        else:
                            stats = self.controlador.obtener_estadisticas()
                            puede_avanzar = stats[calle.value]['color'] == ColorSemaforo.VERDE.value
                        
                        if puede_avanzar and self.vehiculos_animados[calle].index(v_anim) == 0:
                            pos = self.posiciones_espera[calle]
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
            "Bus": TipoVehiculo.BUS,
            "Camión": TipoVehiculo.CAMION,
            "Ambulancia": TipoVehiculo.AMBULANCIA,
            "Policía": TipoVehiculo.POLICIA,
            "Bombero": TipoVehiculo.BOMBERO
        }
        
        vehiculo = self.generador.generar_vehiculo(tipo=tipos[tipo_str])
        self.controlador.agregar_vehiculo_seguro(vehiculo)
        
        if vehiculo.es_emergencia:
            print(f"🚨🚨🚨 {vehiculo} - ¡PRIORIDAD MÁXIMA! 🚨🚨🚨")
        else:
            print(f"➕ {vehiculo}")


def main():
    print("\n" + "="*80)
    print("🚦 SISTEMA DE TRÁFICO - CUENCA, ECUADOR")
    print("="*80)
    print("📍 Manzana: Pío Bravo - María Arizaga - Tarqui - Juan Montalvo")
    print("="*80 + "\n")
    
    root = ctk.CTk()
    app = TrafficGUICuenca(root)
    
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
