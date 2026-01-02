"""
Implementación con Threading (Hilos)
Optimizado para Python 3.13+ sin GIL
"""

import threading
import time
from typing import Dict
from traffic_system import ControladorCentral, Direccion, ColorSemaforo


class ControladorThreading(ControladorCentral):
    """Controlador de tráfico usando hilos"""
    
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.lock_emergencia = threading.Lock()
        self.threads: Dict[str, threading.Thread] = {}
        self.activo = False
    
    def iniciar(self):
        """Inicia el sistema con 7 hilos"""
        if self.activo:
            print("⚠️  El sistema ya está activo")
            return
        
        print("\n🚦 Iniciando sistema con THREADING (Hilos)")
        print("=" * 70)
        self.activo = True
        
        # Hilo controlador de semáforos
        self.threads['controlador'] = threading.Thread(
            target=self._ciclo_semaforos,
            name="Controlador-Semaforos",
            daemon=True
        )
        self.threads['controlador'].start()
        
        # Hilo para cada calle
        for direccion in Direccion:
            thread = threading.Thread(
                target=self._procesar_calle,
                args=(direccion,),
                name=f"Calle-{direccion.value}",
                daemon=True
            )
            self.threads[direccion.value] = thread
            thread.start()
        
        # Hilo monitor de emergencias
        self.threads['emergencias'] = threading.Thread(
            target=self._monitorear_emergencias,
            name="Monitor-Emergencias",
            daemon=True
        )
        self.threads['emergencias'].start()
        
        # Hilo monitor de estado
        self.threads['estado'] = threading.Thread(
            target=self._mostrar_estado_periodico,
            name="Monitor-Estado",
            daemon=True
        )
        self.threads['estado'].start()
        
        print(f"✅ Sistema iniciado con {len(self.threads)} hilos")
        print("=" * 70 + "\n")
    
    def detener(self):
        if not self.activo:
            return
        
        print("\n🛑 Deteniendo sistema...")
        self.activo = False
        
        for nombre, thread in self.threads.items():
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        print("✅ Sistema detenido\n")
        self.mostrar_estado()
        self._mostrar_estadisticas_finales()
    
    def _ciclo_semaforos(self):
        """Controla el ciclo de cambio de semáforos"""
        grupo_activo = 0
        
        while self.activo:
            try:
                with self.lock:
                    direccion_emergencia = self.verificar_emergencias()
                    
                    if direccion_emergencia:
                        pass
                    else:
                        self.cambiar_semaforo_ciclico(grupo_activo)
                
                # Manejar emergencia fuera del lock
                if direccion_emergencia:
                    with self.lock_emergencia:
                        self.manejar_emergencia(direccion_emergencia)
                    continue
                
                time.sleep(self.tiempo_verde_normal)
                
                # Cambiar a amarillo
                with self.lock:
                    if grupo_activo == 0:
                        self.calles[Direccion.NORTE].semaforo.cambiar_color(ColorSemaforo.AMARILLO)
                        self.calles[Direccion.SUR].semaforo.cambiar_color(ColorSemaforo.AMARILLO)
                    else:
                        self.calles[Direccion.ESTE].semaforo.cambiar_color(ColorSemaforo.AMARILLO)
                        self.calles[Direccion.OESTE].semaforo.cambiar_color(ColorSemaforo.AMARILLO)
                
                time.sleep(self.tiempo_amarillo)
                grupo_activo = 1 - grupo_activo
                
            except Exception as e:
                print(f"❌ Error en ciclo de semáforos: {e}")
                time.sleep(1)
    
    def _procesar_calle(self, direccion: Direccion):
        """Procesa vehículos en una calle"""
        calle = self.calles[direccion]
        
        while self.activo:
            try:
                with self.lock:
                    calle.procesar_vehiculo()
                
                time.sleep(0.3)
                
            except Exception as e:
                print(f"❌ Error procesando calle {direccion.value}: {e}")
                time.sleep(1)
    
    def _monitorear_emergencias(self):
        """Monitorea constantemente emergencias"""
        while self.activo:
            try:
                hay_emergencia = any(
                    calle.cola.tiene_emergencia() 
                    for calle in self.calles.values()
                )
                
                if hay_emergencia:
                    time.sleep(0.1)
                else:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"❌ Error monitoreando emergencias: {e}")
                time.sleep(1)
    
    def _mostrar_estado_periodico(self):
        """Muestra el estado cada 10 segundos"""
        contador = 0
        while self.activo:
            try:
                time.sleep(10)
                contador += 1
                
                with self.lock:
                    print(f"\n📊 Actualización #{contador}")
                    self.mostrar_estado()
                    
            except Exception as e:
                print(f"❌ Error mostrando estado: {e}")
    
    def _mostrar_estadisticas_finales(self):
        print("\n📈 ESTADÍSTICAS FINALES")
        print("=" * 70)
        
        stats = self.obtener_estadisticas()
        total_pasados = 0
        total_esperando = 0
        
        for direccion, data in stats.items():
            print(f"{direccion}:")
            print(f"  - Vehículos que pasaron: {data['pasados']}")
            print(f"  - Vehículos esperando: {data['esperando']}")
            print(f"  - Emergencias pendientes: {data['emergencias']}")
            total_pasados += data['pasados']
            total_esperando += data['esperando']
        
        print("-" * 70)
        print(f"TOTAL - Pasados: {total_pasados} | Esperando: {total_esperando}")
        print("=" * 70 + "\n")
    
    def agregar_vehiculo_seguro(self, vehiculo):
        """Agrega un vehículo de forma thread-safe"""
        with self.lock:
            self.agregar_vehiculo(vehiculo)
