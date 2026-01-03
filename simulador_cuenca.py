import random
import time

from traffic_system_cuenca import CalleCuenca, TipoVehiculo, Vehiculo


class GeneradorVehiculosCuenca:
    """Genera vehículos para las calles de Cuenca"""
    
    def __init__(self):
        self.contador = 0
    
    def generar_vehiculo(self, tipo: TipoVehiculo = None, calle: CalleCuenca = None) -> Vehiculo:
        """Genera un vehículo aleatorio o específico"""
        self.contador += 1
        
        if not tipo:
            tipo = random.choice([
                TipoVehiculo.AUTO,
                TipoVehiculo.AUTO,
                TipoVehiculo.AUTO,
                TipoVehiculo.MOTO,
                TipoVehiculo.MOTO,
                TipoVehiculo.BUS,
                TipoVehiculo.CAMION
            ])
        
        if not calle:
            calle = random.choice(list(CalleCuenca))
        
        return Vehiculo(
            id=f"{self.contador:03d}",
            tipo=tipo,
            calle=calle,
            tiempo_llegada=time.time()
        )
    
    def generar_emergencia(self, calle: CalleCuenca = None) -> Vehiculo:
        """Genera un vehículo de emergencia"""
        self.contador += 1
        
        tipo = random.choice([
            TipoVehiculo.AMBULANCIA,
            TipoVehiculo.POLICIA,
            TipoVehiculo.BOMBERO
        ])
        
        if not calle:
            calle = random.choice(list(CalleCuenca))
        
        return Vehiculo(
            id=f"{self.contador:03d}",
            tipo=tipo,
            calle=calle,
            tiempo_llegada=time.time()
        )
