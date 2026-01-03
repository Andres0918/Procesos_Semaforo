import threading
import time
import sys
import platform
import os

from traffic_system_cuenca import (
    CalleCuenca, ColorSemaforo, TipoVehiculo, Vehiculo,
    ColaVehiculos, ControladorCentral
)


class SemaforoThread(threading.Thread):
    """Cada semáforo como hilo independiente"""
    
    def __init__(self, calle: CalleCuenca, controlador):
        super().__init__(daemon=True, name=f"Semaforo-{calle.value}")
        self.calle = calle
        self.controlador = controlador
        self.color = ColorSemaforo.ROJO
        self.bloqueado = False
        self.activo = True
        
        self.lock = threading.RLock()
        self.cola_vehiculos = ColaVehiculos(calle)
        
        print(f"🧵 Hilo creado: {self.name}")
    
    def run(self):
        print(f"▶️ Hilo iniciado: {self.name}")
        
        while self.activo:
            try:
                if self.color == ColorSemaforo.VERDE and not self.bloqueado:
                    self.procesar_vehiculos()
                time.sleep(0.1)
            except Exception as e:
                print(f"❌ Error en {self.name}: {e}")
                break
        
        print(f"⏹️ Hilo detenido: {self.name}")
    
    def cambiar_color(self, nuevo_color: ColorSemaforo):
        with self.lock:
            if self.color != nuevo_color:
                self.color = nuevo_color
                print(f"🚦 {self.calle.value}: {nuevo_color.value}")
    
    def bloquear(self):
        with self.lock:
            self.bloqueado = True
            self.color = ColorSemaforo.ROJO
    
    def desbloquear(self):
        with self.lock:
            self.bloqueado = False
    
    def agregar_vehiculo(self, vehiculo: Vehiculo):
        with self.lock:
            self.cola_vehiculos.agregar_vehiculo(vehiculo)
            
            if vehiculo.es_emergencia:
                print(f"🚨 {vehiculo} llegó a {self.calle.value} - ¡EMERGENCIA!")
            else:
                print(f"🚗 {vehiculo} llegó a {self.calle.value}")
    
    def procesar_vehiculos(self):
        with self.lock:
            vehiculo = self.cola_vehiculos.obtener_proximo()
            
            if vehiculo:
                if vehiculo.es_emergencia:
                    self.cola_vehiculos.remover_vehiculo()
                    print(f"🚨 {vehiculo} pasó por {self.calle.value} [EMERGENCIA]")
                    return True
                
                if self.color == ColorSemaforo.VERDE and not self.bloqueado:
                    self.cola_vehiculos.remover_vehiculo()
                    tiempo_espera = time.time() - vehiculo.tiempo_llegada
                    print(f"✅ {vehiculo} pasó por {self.calle.value} "
                          f"(esperó {tiempo_espera:.1f}s)")
                    return True
            
            return False
    
    def detener(self):
        self.activo = False
    
    def obtener_estadisticas(self):
        with self.lock:
            return {
                'esperando': self.cola_vehiculos.cantidad_esperando(),
                'pasados': self.cola_vehiculos.vehiculos_pasados,
                'emergencias': sum(1 for v in self.cola_vehiculos.vehiculos if v.es_emergencia),
                'color': self.color.value
            }


class ControladorThreadingCuenca(ControladorCentral):
    """Controlador con hilos para Cuenca"""
    
    def __init__(self):
        print("\n" + "="*80)
        print("🧵 CONTROLADOR THREADING - CUENCA, ECUADOR")
        print("="*80)
        
        self.mostrar_info_sistema()
        
        self.lock_global = threading.Lock()
        self.condition_emergencia = threading.Condition()
        self.barrier_ciclo = threading.Barrier(5)
        
        self.semaforos = {}
        for calle in CalleCuenca:
            self.semaforos[calle] = SemaforoThread(calle, self)
        
        self.tiempo_verde_normal = 5.0
        self.tiempo_amarillo = 2.0
        self.activo = False
        
        self.thread_controlador = None
        self.thread_emergencias = None
        
        print("="*80 + "\n")
    
    def mostrar_info_sistema(self):
        print(f"📍 Ciudad: Cuenca, Ecuador")
        print(f"📍 Manzana: Pío Bravo - María Arizaga - Tarqui - Juan Montalvo")
        print(f"📌 Python: {platform.python_version()}")
        
        try:
            gil_enabled = sys._is_gil_enabled() if hasattr(sys, '_is_gil_enabled') else True
            print(f"📌 GIL: {'Habilitado' if gil_enabled else 'Deshabilitado'}")
        except:
            print(f"📌 GIL: Habilitado")
        
        print(f"📌 OS: {platform.system()} {platform.release()}")
        print(f"📌 Núcleos: {os.cpu_count()}")
        print(f"📌 Mecanismos: Lock, RLock, Condition, Barrier")
    
    def iniciar(self):
        print("🚀 Iniciando sistema con HILOS...")
        print("="*80)
        
        self.activo = True
        
        for semaforo in self.semaforos.values():
            semaforo.start()
        
        self.thread_controlador = threading.Thread(
            target=self.ciclo_semaforos,
            daemon=True,
            name="Controlador-Central"
        )
        self.thread_controlador.start()
        
        self.thread_emergencias = threading.Thread(
            target=self.monitor_emergencias,
            daemon=True,
            name="Monitor-Emergencias"
        )
        self.thread_emergencias.start()
        
        print(f"✅ Sistema iniciado con {len(self.semaforos) + 2} hilos")
        print("="*80 + "\n")
    
    def ciclo_semaforos(self):
        ciclo = 0
        
        while self.activo:
            try:
                ciclo += 1
                grupo_activo = ciclo % 2
                
                with self.lock_global:
                    if grupo_activo == 0:
                        print(f"\n🔄 Ciclo {ciclo}: Pío Bravo ↔ María Arizaga (VERDE)")
                        self.semaforos[CalleCuenca.PIO_BRAVO].cambiar_color(ColorSemaforo.VERDE)
                        self.semaforos[CalleCuenca.MARIA_ARIZAGA].cambiar_color(ColorSemaforo.VERDE)
                        self.semaforos[CalleCuenca.TARQUI].cambiar_color(ColorSemaforo.ROJO)
                        self.semaforos[CalleCuenca.JUAN_MONTALVO].cambiar_color(ColorSemaforo.ROJO)
                    else:
                        print(f"\n🔄 Ciclo {ciclo}: Tarqui ↔ Juan Montalvo (VERDE)")
                        self.semaforos[CalleCuenca.TARQUI].cambiar_color(ColorSemaforo.VERDE)
                        self.semaforos[CalleCuenca.JUAN_MONTALVO].cambiar_color(ColorSemaforo.VERDE)
                        self.semaforos[CalleCuenca.PIO_BRAVO].cambiar_color(ColorSemaforo.ROJO)
                        self.semaforos[CalleCuenca.MARIA_ARIZAGA].cambiar_color(ColorSemaforo.ROJO)
                
                time.sleep(self.tiempo_verde_normal)
                
                with self.lock_global:
                    for semaforo in self.semaforos.values():
                        if semaforo.color == ColorSemaforo.VERDE:
                            semaforo.cambiar_color(ColorSemaforo.AMARILLO)
                
                time.sleep(self.tiempo_amarillo)
                
                try:
                    self.barrier_ciclo.wait(timeout=2.0)
                except threading.BrokenBarrierError:
                    pass
                
            except Exception as e:
                print(f"❌ Error en ciclo: {e}")
                break
    
    def monitor_emergencias(self):
        while self.activo:
            try:
                calle_emergencia = None
                
                for calle, semaforo in self.semaforos.items():
                    if semaforo.cola_vehiculos.tiene_emergencia():
                        calle_emergencia = calle
                        break
                
                if calle_emergencia:
                    with self.condition_emergencia:
                        self.manejar_emergencia(calle_emergencia)
                        self.condition_emergencia.notify_all()
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error en monitor: {e}")
                break
    
    def manejar_emergencia(self, calle_emergencia: CalleCuenca):
        print(f"\n🚨🚨🚨 EMERGENCIA EN {calle_emergencia.value.upper()} 🚨🚨🚨")
        
        with self.lock_global:
            for calle, semaforo in self.semaforos.items():
                if calle == calle_emergencia:
                    semaforo.cambiar_color(ColorSemaforo.VERDE)
                else:
                    semaforo.bloquear()
            
            time.sleep(2.0)
            
            semaforo_emergencia = self.semaforos[calle_emergencia]
            while semaforo_emergencia.cola_vehiculos.tiene_emergencia():
                semaforo_emergencia.procesar_vehiculos()
                time.sleep(0.5)
            
            for semaforo in self.semaforos.values():
                semaforo.desbloquear()
            
            print(f"✅ Emergencia completada\n")
    
    def detener(self):
        print("\n🛑 Deteniendo sistema...")
        
        self.activo = False
        
        for semaforo in self.semaforos.values():
            semaforo.detener()
        
        time.sleep(1.0)
        self.mostrar_estadisticas_finales()
        
        print("✅ Sistema detenido\n")
    
    def agregar_vehiculo_seguro(self, vehiculo: Vehiculo):
        self.semaforos[vehiculo.calle].agregar_vehiculo(vehiculo)
    
    def obtener_estadisticas(self):
        stats = {}
        for calle, semaforo in self.semaforos.items():
            stats[calle.value] = semaforo.obtener_estadisticas()
        return stats
    
    def mostrar_estadisticas_finales(self):
        print("\n" + "="*80)
        print("📊 ESTADÍSTICAS FINALES - CUENCA")
        print("="*80)
        
        total_vehiculos = 0
        
        for calle, semaforo in self.semaforos.items():
            stats = semaforo.obtener_estadisticas()
            print(f"\n{calle.value}:")
            print(f"  • Vehículos procesados: {stats['pasados']}")
            print(f"  • Esperando: {stats['esperando']}")
            
            total_vehiculos += stats['pasados']
        
        print(f"\n{'='*80}")
        print(f"Total vehículos: {total_vehiculos}")
        print("="*80 + "\n")
