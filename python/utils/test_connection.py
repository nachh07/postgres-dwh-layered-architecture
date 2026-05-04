"""
Test de conexión a PostgreSQL
"""
import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from python.config.database import test_connection

if __name__ == "__main__":
    print("🔍 Probando conexión a PostgreSQL...")
    print("-" * 50)
    
    if test_connection():
        print("-" * 50)
        print("✅ ¡Conexión exitosa! Puedes ejecutar el pipeline.")
        exit(0)
    else:
        print("-" * 50)
        print("❌ Error de conexión. Verifica:")
        print("   1. PostgreSQL está corriendo")
        print("   2. El archivo config/.env tiene la password correcta")
        print("   3. La base 'data_engineering' existe")
        exit(1)
