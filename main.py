#!/usr/bin/env python3
"""
Sistema de Control de Tráfico - Archivo Principal
Permite seleccionar entre Threading y Multiprocessing
"""

import sys
import time
from traffic_system import ModoParalelismo
from controlador_threading import ControladorThreading
from controlador_multiprocessing import ControladorMultiprocessing
from simulador import SimuladorTrafico, SimuladorInteractivo


def mostrar_banner():
    """Muestra el banner del sistema"""
    print("\n" + "=" * 70)
    print(" " * 15 + "🚦 SISTEMA DE CONTROL DE TRÁFICO 🚦")
    print("=" * 70)
    print("Sistema de simulación de intersección con 4 calles")
    print("Soporte para vehículos de emergencia con prioridad")
    print("Paralelismo configurable: Threading o Multiprocessing")
    print("=" * 70 + "\n")


def seleccionar_modo_paralelismo() -> ModoParalelismo:
    """Permite al usuario seleccionar el modo de paralelismo"""
    print("📋 Selecciona el modo de paralelismo:")
    print("=" * 70)
    print("1. Threading (Hilos)")
    print("   - Optimizado para Python 3.13+ sin GIL (free-threading)")
    print("   - Menor overhead de memoria")
    print("   - Comunicación más rápida entre componentes")
    print("   - Recomendado para sistemas con GIL desactivado")
    print()
    print("2. Multiprocessing (Procesos)")
    print("   - Paralelismo real independiente del GIL")
    print("   - Mayor aislamiento entre componentes")
    print("   - Usa múltiples cores del CPU")
    print("   - Recomendado para Python estándar con GIL")
    print("=" * 70)
    
    while True:
        try:
            opcion = input("\nSelecciona una opción (1 o 2): ").strip()
            
            if opcion == "1":
                return ModoParalelismo.THREADING
            elif opcion == "2":
                return ModoParalelismo.MULTIPROCESSING
            else:
                print("❌ Opción inválida. Por favor selecciona 1 o 2.")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Operación cancelada por el usuario")
            sys.exit(0)


def seleccionar_modo_simulacion() -> str:
    """Permite seleccionar el modo de simulación"""
    print("\n📋 Selecciona el modo de simulación:")
    print("=" * 70)
    print("1. Automático - Simulación con duración específica")
    print("2. Interactivo - Control manual de vehículos")
    print("=" * 70)
    
    while True:
        try:
            opcion = input("\nSelecciona una opción (1 o 2): ").strip()
            
            if opcion in ["1", "2"]:
                return opcion
            else:
                print("❌ Opción inválida. Por favor selecciona 1 o 2.")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Operación cancelada por el usuario")
            sys.exit(0)


def ejecutar_simulacion_automatica(controlador):
    """Ejecuta la simulación automática"""
    print("\n⚙️  Configuración de simulación automática:")
    
    try:
        duracion = int(input("Duración de la simulación (segundos) [30]: ").strip() or "30")
        intervalo = float(input("Intervalo entre vehículos (segundos) [1.5]: ").strip() or "1.5")
    except ValueError:
        print("⚠️  Valores inválidos, usando valores por defecto")
        duracion = 30
        intervalo = 1.5
    
    # Crear y ejecutar simulador
    simulador = SimuladorTrafico(controlador, intervalo_vehiculo=intervalo)
    
    try:
        simulador.iniciar(duracion=duracion)
    except KeyboardInterrupt:
        print("\n⚠️  Simulación interrumpida")
    finally:
        time.sleep(2)  # Dar tiempo para procesar vehículos restantes


def ejecutar_simulacion_interactiva(controlador):
    """Ejecuta la simulación interactiva"""
    simulador = SimuladorInteractivo(controlador)
    
    try:
        simulador.ejecutar()
    except KeyboardInterrupt:
        print("\n⚠️  Modo interactivo interrumpido")


def main():
    """Función principal"""
    try:
        mostrar_banner()
        
        # Seleccionar modo de paralelismo
        modo = seleccionar_modo_paralelismo()
        
        # Crear controlador según el modo seleccionado
        if modo == ModoParalelismo.THREADING:
            print("\n✅ Modo seleccionado: THREADING (Hilos)")
            controlador = ControladorThreading()
        else:
            print("\n✅ Modo seleccionado: MULTIPROCESSING (Procesos)")
            controlador = ControladorMultiprocessing()
        
        # Iniciar el sistema
        controlador.iniciar()
        time.sleep(2)  # Dar tiempo para que se inicien todos los componentes
        
        # Seleccionar modo de simulación
        modo_sim = seleccionar_modo_simulacion()
        
        if modo_sim == "1":
            ejecutar_simulacion_automatica(controlador)
        else:
            ejecutar_simulacion_interactiva(controlador)
        
        # Detener el sistema
        print("\n🛑 Finalizando sistema...")
        controlador.detener()
        
        print("\n✅ Sistema finalizado correctamente")
        print("👋 ¡Gracias por usar el Sistema de Control de Tráfico!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrumpido por el usuario")
        if 'controlador' in locals():
            controlador.detener()
    
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        if 'controlador' in locals():
            controlador.detener()
        sys.exit(1)


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # Necesario para Windows
    main()
