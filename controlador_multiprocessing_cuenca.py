import multiprocessing as mp
from multiprocessing import Process, Queue, Pipe, Semaphore, Manager
import time
import sys
import platform
import os

from traffic_system_cuenca import CalleCuenca, ColorSemaforo, TipoVehiculo


def proceso_semaforo(calle: CalleCuenca, pipe_conn, queue_vehiculos, semaphore, 
                     estado_compartido, activo_flag):
    """Función que ejecuta cada proceso de semáforo"""
    print(f"⚙️ Proceso iniciado: Semaforo-{calle.value} (PID: {os.getpid()})")
    
    cola_vehiculos = []
    vehiculos_pasados = 0
    color_actual = ColorSemaforo.ROJO
    bloqueado = False
    
    while activo_flag.value:
        try:
            # Recibir vehículos
            while not queue_vehiculos.empty():
                try:
                    vehiculo_data = queue_vehiculos.get_nowait()
                    cola_vehiculos.append(vehiculo_data)
                    
                    if vehiculo_data['es_emergencia']:
                        print(f"🚨 {vehiculo_data['tipo']}-{vehiculo_data['id']} "
                              f"llegó a {calle.value} - ¡EMERGENCIA!")
                    else:
                        print(f"🚗 {vehiculo_data['tipo']}-{vehiculo_data['id']} "
                              f"llegó a {calle.value}")
                except:
                    break
            
            # Recibir comandos
            if pipe_conn.poll():
                comando = pipe_conn.recv()
                
                if comando['tipo'] == 'cambiar_color':
                    color_actual = ColorSemaforo(comando['color'])
                    print(f"🚦 {calle.value}: {color_actual.value}")
                
                elif comando['tipo'] == 'bloquear':
                    bloqueado = True
                    color_actual = ColorSemaforo.ROJO
                
                elif comando['tipo'] == 'desbloquear':
                    bloqueado = False
            
            # Procesar vehículos
            if color_actual == ColorSemaforo.VERDE and not bloqueado and cola_vehiculos:
                if semaphore.acquire(block=False):  # block en lugar de blocking
                    try:
                        vehiculo = cola_vehiculos[0]
                        
                        if vehiculo['es_emergencia']:
                            cola_vehiculos.pop(0)
                            vehiculos_pasados += 1
                            print(f"🚨 {vehiculo['tipo']}-{vehiculo['id']} "
                                  f"pasó por {calle.value} [EMERGENCIA]")
                        
                        elif color_actual == ColorSemaforo.VERDE:
                            cola_vehiculos.pop(0)
                            vehiculos_pasados += 1
                            tiempo_espera = time.time() - vehiculo['tiempo_llegada']
                            print(f"✅ {vehiculo['tipo']}-{vehiculo['id']} "
                                  f"pasó por {calle.value} (esperó {tiempo_espera:.1f}s)")
                    
                    finally:
                        semaphore.release()
            
            # Actualizar estado compartido
            estado_compartido[calle.value] = {
                'esperando': len(cola_vehiculos),
                'pasados': vehiculos_pasados,
                'emergencias': sum(1 for v in cola_vehiculos if v['es_emergencia']),
                'color': color_actual.value,
                'tiene_emergencia': any(v['es_emergencia'] for v in cola_vehiculos)
            }
            
            time.sleep(0.1)
        
        except Exception as e:
            print(f"❌ Error en proceso {calle.value}: {e}")
            break
    
    print(f"⏹️ Proceso detenido: Semaforo-{calle.value}")


class ControladorMultiprocessingCuenca:
    """Controlador con procesos para Cuenca"""
    
    def __init__(self):
        print("\n" + "="*80)
        print("⚙️ CONTROLADOR MULTIPROCESSING - CUENCA, ECUADOR")
        print("="*80)
        
        self.mostrar_info_sistema()
        
        self.manager = Manager()
        self.estado_compartido = self.manager.dict()
        self.semaphore = Semaphore(1)
        self.activo_flag = self.manager.Value('i', 1)
        
        self.queues_vehiculos = {}
        self.pipes = {}
        self.procesos = {}
        
        for calle in CalleCuenca:
            self.queues_vehiculos[calle] = Queue()
            parent_conn, child_conn = Pipe()
            self.pipes[calle] = (parent_conn, child_conn)
            
            self.estado_compartido[calle.value] = {
                'esperando': 0,
                'pasados': 0,
                'emergencias': 0,
                'color': ColorSemaforo.ROJO.value,
                'tiene_emergencia': False
            }
            
            proceso = Process(
                target=proceso_semaforo,
                args=(calle, child_conn, self.queues_vehiculos[calle],
                      self.semaphore, self.estado_compartido, self.activo_flag),
                name=f"Semaforo-{calle.value}",
                daemon=True
            )
            self.procesos[calle] = proceso
        
        self.tiempo_verde_normal = 5.0
        self.tiempo_amarillo = 2.0
        self.activo = False
        
        self.proceso_controlador = None
        self.proceso_emergencias = None
        
        print("="*80 + "\n")
    
    def mostrar_info_sistema(self):
        print(f"📍 Ciudad: Cuenca, Ecuador")
        print(f"📍 Manzana: Pío Bravo - María Arizaga - Tarqui - Juan Montalvo")
        print(f"📌 Python: {platform.python_version()}")
        print(f"📌 GIL: No aplica (procesos independientes)")
        print(f"📌 OS: {platform.system()} {platform.release()}")
        print(f"📌 Núcleos: {os.cpu_count()}")
        print(f"📌 Mecanismos: Queue, Pipe, Semaphore, Manager")
    
    def iniciar(self):
        print("🚀 Iniciando sistema con PROCESOS...")
        print("="*80)
        
        self.activo = True
        self.activo_flag.value = 1
        
        # Iniciar procesos de semáforos
        for proceso in self.procesos.values():
            proceso.start()
            print(f"▶️ Proceso iniciado: {proceso.name} (PID: {proceso.pid})")
        
        # En lugar de crear procesos separados, usamos hilos para el controlador
        # Esto evita el problema de pickle en Windows
        import threading
        
        self.thread_controlador = threading.Thread(
            target=self.ciclo_semaforos,
            daemon=True,
            name="Controlador-Central"
        )
        self.thread_controlador.start()
        print(f"▶️ Hilo iniciado: Controlador-Central")
        
        self.thread_emergencias = threading.Thread(
            target=self.monitor_emergencias,
            daemon=True,
            name="Monitor-Emergencias"
        )
        self.thread_emergencias.start()
        print(f"▶️ Hilo iniciado: Monitor-Emergencias")
        
        print(f"✅ Sistema iniciado: {len(self.procesos)} procesos + 2 hilos")
        print("="*80 + "\n")
    
    def ciclo_semaforos(self):
        ciclo = 0
        
        while self.activo_flag.value:
            try:
                ciclo += 1
                grupo_activo = ciclo % 2
                
                if grupo_activo == 0:
                    print(f"\n🔄 Ciclo {ciclo}: Pío Bravo ↔ María Arizaga (VERDE)")
                    self.enviar_comando(CalleCuenca.PIO_BRAVO, 'cambiar_color', ColorSemaforo.VERDE)
                    self.enviar_comando(CalleCuenca.MARIA_ARIZAGA, 'cambiar_color', ColorSemaforo.VERDE)
                    self.enviar_comando(CalleCuenca.TARQUI, 'cambiar_color', ColorSemaforo.ROJO)
                    self.enviar_comando(CalleCuenca.JUAN_MONTALVO, 'cambiar_color', ColorSemaforo.ROJO)
                else:
                    print(f"\n🔄 Ciclo {ciclo}: Tarqui ↔ Juan Montalvo (VERDE)")
                    self.enviar_comando(CalleCuenca.TARQUI, 'cambiar_color', ColorSemaforo.VERDE)
                    self.enviar_comando(CalleCuenca.JUAN_MONTALVO, 'cambiar_color', ColorSemaforo.VERDE)
                    self.enviar_comando(CalleCuenca.PIO_BRAVO, 'cambiar_color', ColorSemaforo.ROJO)
                    self.enviar_comando(CalleCuenca.MARIA_ARIZAGA, 'cambiar_color', ColorSemaforo.ROJO)
                
                time.sleep(self.tiempo_verde_normal)
                
                for calle in CalleCuenca:
                    if self.estado_compartido[calle.value]['color'] == ColorSemaforo.VERDE.value:
                        self.enviar_comando(calle, 'cambiar_color', ColorSemaforo.AMARILLO)
                
                time.sleep(self.tiempo_amarillo)
            
            except Exception as e:
                print(f"❌ Error en ciclo: {e}")
                break
    
    def monitor_emergencias(self):
        while self.activo_flag.value:
            try:
                for calle in CalleCuenca:
                    if self.estado_compartido[calle.value]['tiene_emergencia']:
                        self.manejar_emergencia(calle)
                        break
                
                time.sleep(0.5)
            
            except Exception as e:
                print(f"❌ Error en monitor: {e}")
                break
    
    def enviar_comando(self, calle: CalleCuenca, tipo: str, color: ColorSemaforo = None):
        try:
            comando = {'tipo': tipo}
            if color:
                comando['color'] = color.value
            
            self.pipes[calle][0].send(comando)
        except:
            pass
    
    def manejar_emergencia(self, calle_emergencia: CalleCuenca):
        print(f"\n🚨🚨🚨 EMERGENCIA EN {calle_emergencia.value.upper()} 🚨🚨🚨")
        
        for calle in CalleCuenca:
            if calle == calle_emergencia:
                self.enviar_comando(calle, 'cambiar_color', ColorSemaforo.VERDE)
            else:
                self.enviar_comando(calle, 'bloquear')
        
        time.sleep(2.0)
        
        while self.estado_compartido[calle_emergencia.value]['tiene_emergencia']:
            time.sleep(0.5)
        
        for calle in CalleCuenca:
            self.enviar_comando(calle, 'desbloquear')
        
        print(f"✅ Emergencia completada\n")
    
    def detener(self):
        print("\n🛑 Deteniendo sistema...")
        
        self.activo = False
        self.activo_flag.value = 0
        
        time.sleep(1.0)
        
        # Detener procesos de semáforos
        for proceso in self.procesos.values():
            if proceso.is_alive():
                proceso.terminate()
        
        # Los hilos se detendrán solos (daemon=True)
        
        self.mostrar_estadisticas_finales()
        
        print("✅ Sistema detenido\n")
    
    def agregar_vehiculo_seguro(self, vehiculo):
        vehiculo_data = {
            'id': vehiculo.id,
            'tipo': vehiculo.tipo.value,
            'calle': vehiculo.calle.value,
            'tiempo_llegada': vehiculo.tiempo_llegada,
            'es_emergencia': vehiculo.es_emergencia
        }
        
        self.queues_vehiculos[vehiculo.calle].put(vehiculo_data)
    
    def obtener_estadisticas(self):
        return dict(self.estado_compartido)
    
    def mostrar_estadisticas_finales(self):
        print("\n" + "="*80)
        print("📊 ESTADÍSTICAS FINALES - CUENCA")
        print("="*80)
        
        total_vehiculos = 0
        
        for calle in CalleCuenca:
            stats = self.estado_compartido[calle.value]
            print(f"\n{calle.value}:")
            print(f"  • Vehículos procesados: {stats['pasados']}")
            print(f"  • Esperando: {stats['esperando']}")
            
            total_vehiculos += stats['pasados']
        
        print(f"\n{'='*80}")
        print(f"Total vehículos: {total_vehiculos}")
        print("="*80 + "\n")
