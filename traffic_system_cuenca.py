from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import time
from abc import ABC, abstractmethod


class CalleCuenca(Enum):
    """Calles de la manzana en Cuenca"""
    PIO_BRAVO = "Pío Bravo"  # Sur (abajo)
    MARIA_ARIZAGA = "María Arizaga"  # Norte (arriba)
    TARQUI = "Tarqui"  # Este (derecha)
    JUAN_MONTALVO = "Juan Montalvo"  # Oeste (izquierda)


class ColorSemaforo(Enum):
    """Estados del semáforo"""
    ROJO = "Rojo"
    AMARILLO = "Amarillo"
    VERDE = "Verde"


class TipoVehiculo(Enum):
    """Tipos de vehículos"""
    AUTO = "Auto"
    MOTO = "Moto"
    CAMION = "Camión"
    BUS = "Bus"
    AMBULANCIA = "Ambulancia"
    POLICIA = "Policía"
    BOMBERO = "Bombero"


@dataclass
class Vehiculo:
    """Representa un vehículo en el sistema"""
    id: str
    tipo: TipoVehiculo
    calle: CalleCuenca
    tiempo_llegada: float
    es_emergencia: bool = False
    
    def __post_init__(self):
        self.es_emergencia = self.tipo in [
            TipoVehiculo.AMBULANCIA,
            TipoVehiculo.POLICIA,
            TipoVehiculo.BOMBERO
        ]
    
    def __repr__(self):
        emergencia = " [EMERGENCIA]" if self.es_emergencia else ""
        return f"{self.tipo.value}-{self.id}{emergencia}"


class EstadoSemaforo:
    """Controla el estado de un semáforo"""
    
    def __init__(self, calle: CalleCuenca):
        self.calle = calle
        self.color = ColorSemaforo.ROJO
        self.tiempo_cambio = 0.0
        self.bloqueado_emergencia = False
    
    def cambiar_color(self, nuevo_color: ColorSemaforo):
        self.color = nuevo_color
        self.tiempo_cambio = time.time()
    
    def bloquear_para_emergencia(self):
        self.bloqueado_emergencia = True
        self.cambiar_color(ColorSemaforo.ROJO)
    
    def desbloquear_emergencia(self):
        self.bloqueado_emergencia = False
    
    def puede_avanzar(self) -> bool:
        return self.color == ColorSemaforo.VERDE and not self.bloqueado_emergencia
    
    def __repr__(self):
        emergencia = " [BLOQUEADO]" if self.bloqueado_emergencia else ""
        return f"Semáforo {self.calle.value}: {self.color.value}{emergencia}"


class ColaVehiculos:
    """Gestiona la cola de vehículos en una calle"""
    
    def __init__(self, calle: CalleCuenca):
        self.calle = calle
        self.vehiculos: List[Vehiculo] = []
        self.vehiculos_pasados = 0
    
    def agregar_vehiculo(self, vehiculo: Vehiculo):
        self.vehiculos.append(vehiculo)
        self.vehiculos.sort(
            key=lambda v: (not v.es_emergencia, v.tiempo_llegada)
        )
    
    def tiene_emergencia(self) -> bool:
        return any(v.es_emergencia for v in self.vehiculos)
    
    def obtener_proximo(self) -> Optional[Vehiculo]:
        return self.vehiculos[0] if self.vehiculos else None
    
    def remover_vehiculo(self) -> Optional[Vehiculo]:
        if self.vehiculos:
            vehiculo = self.vehiculos.pop(0)
            self.vehiculos_pasados += 1
            return vehiculo
        return None
    
    def cantidad_esperando(self) -> int:
        return len(self.vehiculos)
    
    def __repr__(self):
        emergencias = sum(1 for v in self.vehiculos if v.es_emergencia)
        return (f"Cola {self.calle.value}: {len(self.vehiculos)} vehículos "
                f"({emergencias} emergencias) - Pasados: {self.vehiculos_pasados}")


class Calle:
    """Representa una calle con su semáforo y cola de vehículos"""
    
    def __init__(self, nombre_calle: CalleCuenca):
        self.nombre = nombre_calle
        self.semaforo = EstadoSemaforo(nombre_calle)
        self.cola = ColaVehiculos(nombre_calle)
    
    def agregar_vehiculo(self, vehiculo: Vehiculo):
        self.cola.agregar_vehiculo(vehiculo)
        
        if vehiculo.es_emergencia:
            print(f"🚨 {vehiculo} llegó a {self.nombre.value} - ¡EMERGENCIA!")
        else:
            print(f"🚗 {vehiculo} llegó a {self.nombre.value}")
    
    def procesar_vehiculo(self) -> bool:
        vehiculo = self.cola.obtener_proximo()
        
        if not vehiculo:
            return False
        
        if vehiculo.es_emergencia:
            self.cola.remover_vehiculo()
            print(f"🚨 {vehiculo} pasó por {self.nombre.value} [EMERGENCIA]")
            return True
        
        if self.semaforo.puede_avanzar():
            self.cola.remover_vehiculo()
            tiempo_espera = time.time() - vehiculo.tiempo_llegada
            print(f"✅ {vehiculo} pasó por {self.nombre.value} "
                  f"(esperó {tiempo_espera:.1f}s)")
            return True
        
        return False
    
    def __repr__(self):
        return f"{self.semaforo} | {self.cola}"


class ControladorCentral(ABC):
    """Clase abstracta para el controlador central"""
    
    def __init__(self):
        self.calles = {
            CalleCuenca.PIO_BRAVO: Calle(CalleCuenca.PIO_BRAVO),
            CalleCuenca.MARIA_ARIZAGA: Calle(CalleCuenca.MARIA_ARIZAGA),
            CalleCuenca.TARQUI: Calle(CalleCuenca.TARQUI),
            CalleCuenca.JUAN_MONTALVO: Calle(CalleCuenca.JUAN_MONTALVO)
        }
        self.tiempo_verde_normal = 5.0
        self.tiempo_amarillo = 2.0
        self.activo = False
    
    @abstractmethod
    def iniciar(self):
        pass
    
    @abstractmethod
    def detener(self):
        pass
    
    def verificar_emergencias(self) -> Optional[CalleCuenca]:
        for calle_enum, calle in self.calles.items():
            if calle.cola.tiene_emergencia():
                return calle_enum
        return None
    
    def manejar_emergencia(self, calle_emergencia: CalleCuenca):
        print(f"\n🚨🚨🚨 EMERGENCIA EN {calle_emergencia.value.upper()} 🚨🚨🚨")
        print("Deteniendo todo el tráfico...")
        
        for calle_enum, calle in self.calles.items():
            if calle_enum == calle_emergencia:
                calle.semaforo.cambiar_color(ColorSemaforo.VERDE)
            else:
                calle.semaforo.bloquear_para_emergencia()
        
        time.sleep(1.5)
        
        calle_obj = self.calles[calle_emergencia]
        while calle_obj.cola.tiene_emergencia():
            calle_obj.procesar_vehiculo()
            time.sleep(0.5)
        
        print(f"✅ Emergencia en {calle_emergencia.value} completada\n")
        
        for calle in self.calles.values():
            calle.semaforo.desbloquear_emergencia()
    
    def cambiar_semaforo_sincronizado(self, grupo_activo: int):
        """
        Cambia semáforos de forma sincronizada
        Grupo 0: Pío Bravo - María Arizaga (Norte-Sur)
        Grupo 1: Tarqui - Juan Montalvo (Este-Oeste)
        """
        if grupo_activo == 0:
            # Norte-Sur en verde
            self.calles[CalleCuenca.PIO_BRAVO].semaforo.cambiar_color(ColorSemaforo.VERDE)
            self.calles[CalleCuenca.MARIA_ARIZAGA].semaforo.cambiar_color(ColorSemaforo.VERDE)
            self.calles[CalleCuenca.TARQUI].semaforo.cambiar_color(ColorSemaforo.ROJO)
            self.calles[CalleCuenca.JUAN_MONTALVO].semaforo.cambiar_color(ColorSemaforo.ROJO)
        else:
            # Este-Oeste en verde
            self.calles[CalleCuenca.TARQUI].semaforo.cambiar_color(ColorSemaforo.VERDE)
            self.calles[CalleCuenca.JUAN_MONTALVO].semaforo.cambiar_color(ColorSemaforo.VERDE)
            self.calles[CalleCuenca.PIO_BRAVO].semaforo.cambiar_color(ColorSemaforo.ROJO)
            self.calles[CalleCuenca.MARIA_ARIZAGA].semaforo.cambiar_color(ColorSemaforo.ROJO)
    
    def mostrar_estado(self):
        print("\n" + "="*80)
        print("ESTADO DEL SISTEMA - MANZANA CUENCA")
        print("="*80)
        for calle in self.calles.values():
            print(calle)
        print("="*80 + "\n")
    
    def agregar_vehiculo(self, vehiculo: Vehiculo):
        self.calles[vehiculo.calle].agregar_vehiculo(vehiculo)
    
    def obtener_estadisticas(self):
        stats = {}
        for calle_enum, calle in self.calles.items():
            stats[calle_enum.value] = {
                'esperando': calle.cola.cantidad_esperando(),
                'pasados': calle.cola.vehiculos_pasados,
                'emergencias': sum(1 for v in calle.cola.vehiculos if v.es_emergencia)
            }
        return stats
