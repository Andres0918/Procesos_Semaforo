"""
Implementación con Multiprocessing (Procesos)
Usa procesos separados para máximo paralelismo
"""

import multiprocessing as mp
from multiprocessing import Process, Queue, Manager, Lock, Event
import time
from typing import Dict
from traffic_system import (
    ControladorCentral, Direccion, Calle, ColorSemaforo,
    Vehiculo, EstadoSemaforo, ColaVehiculos
)


class ControladorMultiprocessing(ControladorCentral):
    """Controlador de tráfico usando procesos (multiprocessing)"""
    
    def __init__(self):
        super().__init__()
        self.manager = Manager()
        self.cola_vehiculos = self.manager.Queue()
        self.cola_emergencias = self.manager.Queue()
        self.lock = self.manager.Lock()
        self.evento_parada = self.manager.Event()
        self.procesos: Dict[str, Process] = {}
        self.activo = False
        
        # Estados compartidos entre procesos
        self.estados_semaforos = self.manager.dict()
        self.colas_vehiculos = self.manager.dict()
        self.estadisticas = self.manager.dict()
        
        self._inicializar_estados_compartidos()
    
    def _inicializar_estados_compartidos(self):
        """Inicializa los estados compartidos entre procesos"""
        for direccion in Direccion:
            # Estado de semáforo
            self.estados_semaforos[direccion.value] = {
                'color': ColorSemaforo.ROJO.value,
                'bloqueado': False
            }
            
            # Cola de vehículos (lista compartida)
            self.colas_vehiculos[direccion.value] = self.manager.list()
            
            # Estadísticas
            self.estadisticas[direccion.value] = {
                'esperando': 0,
                'pasados': 0,
                'emergencias': 0
            }
    
    def iniciar(self):
        """Inicia el sistema con procesos"""
        if self.activo:
            print("⚠️  El sistema ya está activo")
            return
        
        print("\n🚦 Iniciando sistema con MULTIPROCESSING (Procesos)")
        print("=" * 70)
        self.activo = True
        self.evento_parada.clear()
        
        # Proceso para el controlador de semáforos
        proceso_controlador = Process(
            target=self._ciclo_semaforos_proceso,
            name="Controlador-Semaforos"
        )
        proceso_controlador.start()
        self.procesos['controlador'] = proceso_controlador
        
        # Proceso para cada calle
        for direccion in Direccion:
            proceso = Process(
                target=self._procesar_calle_proceso,
                args=(direccion,),
                name=f"Calle-{direccion.value}"
            )
            proceso.start()
            self.procesos[direccion.value] = proceso
        
        # Proceso para manejar emergencias
        proceso_emergencias = Process(
            target=self._monitorear_emergencias_proceso,
            name="Monitor-Emergencias"
        )
        proceso_emergencias.start()
        self.procesos['emergencias'] = proceso_emergencias
        
        # Proceso para distribuir vehículos
        proceso_distribuidor = Process(
            target=self._distribuir_vehiculos_proceso,
            name="Distribuidor-Vehiculos"
        )
        proceso_distribuidor.start()
        self.procesos['distribuidor'] = proceso_distribuidor
        
        # Proceso para mostrar estado
        proceso_estado = Process(
            target=self._mostrar_estado_proceso,
            name="Monitor-Estado"
        )
        proceso_estado.start()
        self.procesos['estado'] = proceso_estado
        
        print(f"✅ Sistema iniciado con {len(self.procesos)} procesos")
        print("=" * 70 + "\n")
    
    def detener(self):
        """Detiene el sistema"""
        if not self.activo:
            return
        
        print("\n🛑 Deteniendo sistema...")
        self.activo = False
        self.evento_parada.set()
        
        # Esperar a que los procesos terminen
        for nombre, proceso in self.procesos.items():
            if proceso.is_alive():
                proceso.join(timeout=3.0)
                if proceso.is_alive():
                    proceso.terminate()
                    print(f"⚠️  Proceso {nombre} terminado forzosamente")
        
        print("✅ Sistema detenido\n")
        self._mostrar_estadisticas_finales()
    
    def _ciclo_semaforos_proceso(self):
        """Ciclo principal de control de semáforos (proceso separado)"""
        grupo_activo = 0
        
        while not self.evento_parada.is_set():
            try:
                # Verificar emergencias
                tiene_emergencia = False
                direccion_emergencia = None
                
                for direccion in Direccion:
                    cola = list(self.colas_vehiculos[direccion.value])
                    if any(v.get('es_emergencia', False) for v in cola):
                        tiene_emergencia = True
                        direccion_emergencia = direccion
                        break
                
                if tiene_emergencia:
                    self.cola_emergencias.put(direccion_emergencia)
                    time.sleep(2)  # Esperar a que se maneje la emergencia
                    continue
                
                # Funcionamiento normal - cambiar semáforos
                with self.lock:
                    if grupo_activo == 0:
                        # Norte-Sur en verde
                        self.estados_semaforos[Direccion.NORTE.value]['color'] = ColorSemaforo.VERDE.value
                        self.estados_semaforos[Direccion.SUR.value]['color'] = ColorSemaforo.VERDE.value
                        self.estados_semaforos[Direccion.ESTE.value]['color'] = ColorSemaforo.ROJO.value
                        self.estados_semaforos[Direccion.OESTE.value]['color'] = ColorSemaforo.ROJO.value
                    else:
                        # Este-Oeste en verde
                        self.estados_semaforos[Direccion.ESTE.value]['color'] = ColorSemaforo.VERDE.value
                        self.estados_semaforos[Direccion.OESTE.value]['color'] = ColorSemaforo.VERDE.value
                        self.estados_semaforos[Direccion.NORTE.value]['color'] = ColorSemaforo.ROJO.value
                        self.estados_semaforos[Direccion.SUR.value]['color'] = ColorSemaforo.ROJO.value
                
                # Esperar tiempo de verde
                time.sleep(self.tiempo_verde_normal)
                
                # Cambiar a amarillo
                with self.lock:
                    if grupo_activo == 0:
                        self.estados_semaforos[Direccion.NORTE.value]['color'] = ColorSemaforo.AMARILLO.value
                        self.estados_semaforos[Direccion.SUR.value]['color'] = ColorSemaforo.AMARILLO.value
                    else:
                        self.estados_semaforos[Direccion.ESTE.value]['color'] = ColorSemaforo.AMARILLO.value
                        self.estados_semaforos[Direccion.OESTE.value]['color'] = ColorSemaforo.AMARILLO.value
                
                time.sleep(self.tiempo_amarillo)
                
                # Cambiar grupo
                grupo_activo = 1 - grupo_activo
                
            except Exception as e:
                print(f"❌ Error en ciclo de semáforos: {e}")
                time.sleep(1)
    
    def _procesar_calle_proceso(self, direccion: Direccion):
        """Procesa vehículos en una calle específica (proceso separado)"""
        while not self.evento_parada.is_set():
            try:
                cola = self.colas_vehiculos[direccion.value]
                estado_semaforo = self.estados_semaforos[direccion.value]
                
                if len(cola) > 0:
                    vehiculo_data = cola[0]
                    
                    # Vehículos de emergencia pasan siempre
                    if vehiculo_data.get('es_emergencia', False):
                        with self.lock:
                            cola.pop(0)
                            stats = dict(self.estadisticas[direccion.value])
                            stats['pasados'] += 1
                            stats['esperando'] = len(cola)
                            stats['emergencias'] = sum(1 for v in cola if v.get('es_emergencia', False))
                            self.estadisticas[direccion.value] = stats
                        
                        print(f"🚨 {vehiculo_data['repr']} pasó por {direccion.value} [EMERGENCIA]")
                        time.sleep(0.5)
                        continue
                    
                    # Vehículos normales solo con luz verde
                    if (estado_semaforo['color'] == ColorSemaforo.VERDE.value and 
                        not estado_semaforo['bloqueado']):
                        with self.lock:
                            cola.pop(0)
                            stats = dict(self.estadisticas[direccion.value])
                            stats['pasados'] += 1
                            stats['esperando'] = len(cola)
                            stats['emergencias'] = sum(1 for v in cola if v.get('es_emergencia', False))
                            self.estadisticas[direccion.value] = stats
                        
                        tiempo_espera = time.time() - vehiculo_data['tiempo_llegada']
                        print(f"✅ {vehiculo_data['repr']} pasó por {direccion.value} "
                              f"(esperó {tiempo_espera:.1f}s)")
                
                time.sleep(0.3)
                
            except Exception as e:
                print(f"❌ Error procesando calle {direccion.value}: {e}")
                time.sleep(1)
    
    def _monitorear_emergencias_proceso(self):
        """Monitorea y maneja emergencias (proceso separado)"""
        while not self.evento_parada.is_set():
            try:
                if not self.cola_emergencias.empty():
                    direccion_emergencia = self.cola_emergencias.get(timeout=0.1)
                    
                    print(f"\n🚨🚨🚨 EMERGENCIA DETECTADA EN {direccion_emergencia.value.upper()} 🚨🚨🚨")
                    print("Deteniendo todo el tráfico...")
                    
                    # Bloquear todas las calles excepto la de emergencia
                    with self.lock:
                        for direccion in Direccion:
                            if direccion == direccion_emergencia:
                                self.estados_semaforos[direccion.value]['color'] = ColorSemaforo.VERDE.value
                                self.estados_semaforos[direccion.value]['bloqueado'] = False
                            else:
                                self.estados_semaforos[direccion.value]['color'] = ColorSemaforo.ROJO.value
                                self.estados_semaforos[direccion.value]['bloqueado'] = True
                    
                    # Esperar a que pasen emergencias
                    time.sleep(3)
                    
                    # Desbloquear
                    with self.lock:
                        for direccion in Direccion:
                            self.estados_semaforos[direccion.value]['bloqueado'] = False
                    
                    print(f"✅ Emergencia en {direccion_emergencia.value} completada\n")
                
                time.sleep(0.2)
                
            except Exception as e:
                if "Empty" not in str(e):
                    print(f"❌ Error monitoreando emergencias: {e}")
                time.sleep(0.5)
    
    def _distribuir_vehiculos_proceso(self):
        """Distribuye vehículos entrantes a las colas (proceso separado)"""
        while not self.evento_parada.is_set():
            try:
                if not self.cola_vehiculos.empty():
                    vehiculo = self.cola_vehiculos.get(timeout=0.1)
                    direccion = vehiculo.direccion.value
                    
                    vehiculo_data = {
                        'id': vehiculo.id,
                        'tipo': vehiculo.tipo.value,
                        'direccion': direccion,
                        'tiempo_llegada': vehiculo.tiempo_llegada,
                        'es_emergencia': vehiculo.es_emergencia,
                        'repr': repr(vehiculo)
                    }
                    
                    with self.lock:
                        cola = self.colas_vehiculos[direccion]
                        cola.append(vehiculo_data)
                        
                        # Ordenar: emergencias primero
                        cola_ordenada = sorted(
                            list(cola),
                            key=lambda v: (not v['es_emergencia'], v['tiempo_llegada'])
                        )
                        cola[:] = cola_ordenada
                        
                        # Actualizar estadísticas
                        stats = dict(self.estadisticas[direccion])
                        stats['esperando'] = len(cola)
                        stats['emergencias'] = sum(1 for v in cola if v.get('es_emergencia', False))
                        self.estadisticas[direccion] = stats
                    
                    if vehiculo.es_emergencia:
                        print(f"🚨 {vehiculo} llegó a {direccion} - ¡EMERGENCIA!")
                    else:
                        print(f"🚗 {vehiculo} llegó a {direccion}")
                
                time.sleep(0.1)
                
            except Exception as e:
                if "Empty" not in str(e):
                    print(f"❌ Error distribuyendo vehículos: {e}")
                time.sleep(0.2)
    
    def _mostrar_estado_proceso(self):
        """Muestra el estado periódicamente (proceso separado)"""
        contador = 0
        while not self.evento_parada.is_set():
            try:
                time.sleep(10)
                contador += 1
                
                print(f"\n📊 Actualización periódica #{contador}")
                print("=" * 70)
                print("ESTADO DEL SISTEMA DE TRÁFICO")
                print("=" * 70)
                
                with self.lock:
                    for direccion in Direccion:
                        estado = self.estados_semaforos[direccion.value]
                        stats = self.estadisticas[direccion.value]
                        bloqueado = " [BLOQUEADO]" if estado['bloqueado'] else ""
                        
                        print(f"Semáforo {direccion.value}: {estado['color']}{bloqueado} | "
                              f"Esperando: {stats['esperando']} | Pasados: {stats['pasados']}")
                
                print("=" * 70 + "\n")
                
            except Exception as e:
                print(f"❌ Error mostrando estado: {e}")
    
    def _mostrar_estadisticas_finales(self):
        """Muestra estadísticas finales del sistema"""
        print("\n📈 ESTADÍSTICAS FINALES")
        print("=" * 70)
        
        total_pasados = 0
        total_esperando = 0
        
        for direccion in Direccion:
            stats = self.estadisticas[direccion.value]
            print(f"{direccion.value}:")
            print(f"  - Vehículos que pasaron: {stats['pasados']}")
            print(f"  - Vehículos esperando: {stats['esperando']}")
            print(f"  - Emergencias pendientes: {stats['emergencias']}")
            total_pasados += stats['pasados']
            total_esperando += stats['esperando']
        
        print("-" * 70)
        print(f"TOTAL - Pasados: {total_pasados} | Esperando: {total_esperando}")
        print("=" * 70 + "\n")
    
    def agregar_vehiculo_seguro(self, vehiculo: Vehiculo):
        """Agrega un vehículo a la cola de entrada (process-safe)"""
        self.cola_vehiculos.put(vehiculo)
