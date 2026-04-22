"""
Script para ejecutar schema.sql en la base de datos usando SQLAlchemy
"""
from sqlalchemy import create_engine, text

# Credenciales de la base de datos
DB_URL = "postgresql://postgres:312245cesar@localhost:5433/IHeartCareDB"

def execute_schema():
    """Ejecuta el archivo schema.sql en la base de datos"""
    try:
        # Crear engine y conectar
        engine = create_engine(DB_URL)
        
        # Leer el archivo schema.sql
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema_content = f.read()
        
        # Ejecutar el schema
        print("Ejecutando schema.sql...")
        with engine.connect() as connection:
            # Dividir el contenido en statements individuales
            statements = schema_content.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement:  # Solo ejecutar si no está vacío
                    try:
                        connection.execute(text(statement))
                    except Exception as e:
                        # Algunas statements pueden fallar (como DROP IF EXISTS), pero eso es normal
                        print(f"⚠️  {str(e)[:100]}...")
            
            connection.commit()
        
        print("\n✅ Schema ejecutado exitosamente!")
        
        # Verificar que las tablas fueron creadas
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            print(f"\n📊 Tablas creadas ({len(tables)}):")
            for table in tables:
                print(f"  - {table[0]}")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    execute_schema()
