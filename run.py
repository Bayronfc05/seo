#!/usr/bin/env python3
"""
Script de inicio principal para SEO Content Generator v2.0
Ejecuta el servidor Flask con configuración optimizada
"""

import sys
import os

# Añadir backend al path para que funcionen los imports
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Cambiar al directorio backend para que las rutas relativas funcionen
os.chdir(backend_path)

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 SEO CONTENT GENERATOR v2.0")
    print("=" * 70)
    print("\n📋 Iniciando servidor Flask...")
    print("💡 Modo: DEMO (sin API key de Anthropic)")
    print("🌐 URL: http://localhost:5000")
    print("\n✨ Características disponibles:")
    print("   • Generación de contenido SEO con 5 estrategias")
    print("   • Aprendizaje por Refuerzo (Multi-Armed Bandit)")
    print("   • Métricas SEO completas")
    print("   • Interfaz web interactiva")
    print("\n⚠️  Presiona Ctrl+C para detener el servidor")
    print("=" * 70 + "\n")

    try:
        # Importar aquí después de configurar el path
        from app import main
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Servidor detenido. ¡Hasta pronto!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
