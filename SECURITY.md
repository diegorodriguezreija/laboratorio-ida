# Seguridad

IdA es un proyecto experimental para ejecutar en local. No está pensado para exponerse a una red ni para manejar datos de terceros.

## Componentes con riesgo y medidas por defecto

| Componente | Riesgo | Medida por defecto |
|---|---|---|
| Mundo Bosque (`mundo_bosque_archivos/`) | Sus acciones borran, truncan y escriben ficheros | Solo acepta como raíz un directorio temporal creado para él (prefijo `ida_bosque_` bajo el temporal del sistema); cualquier otra ruta se rechaza, incluido un repositorio clonado dentro del temporal y no hay opción para cambiarlo. Todas las operaciones se confinan a esa raíz (se resuelven `..`, rutas absolutas y enlaces). `main.py` crea su propio directorio temporal y lo borra al terminar. Lo comprueban los tests de `tests_arquitectura/test_seguridad_ejecucion.py` |
| Autopoiesis AST (`nivel_2_sistemas/autopoiesis_ast.py`) | Recompila y sustituye clases en memoria con `exec` | Desactivada por defecto. Solo se activa con `--habilitar-autopoiesis`. No escribe código en disco y tiene rollback en memoria |
| Servidor MCP (`servidor_mcp_telemetria.py`) | Interfaz de control | Es un despachador JSON-RPC **en proceso**: no abre ningún puerto ni escucha en red, y no tiene autenticación. Si algún día se expone por red, debe escuchar solo en `127.0.0.1` |
| Snake web (Playwright) | Automatiza un sitio de terceros (https://playsnake.org/) | Experimental. No usa credenciales. Respeta las condiciones de uso del sitio; si el sitio cambia o deja de funcionar, el mundo deja de funcionar |
| Ollama (LLM local, mundo de ajedrez) | Envía texto a un servicio local en `localhost:11434` | Opcional; si no está disponible se usa la heurística. Se desactiva con `--sin-ollama` |
| Docker de nivel 0 (PostgreSQL + pgvector) | Credenciales y puertos | La contraseña se define en `.env` (copia de `.env.example`, que no tiene valores); el puerto se publica solo en `127.0.0.1`. Ningún módulo se conecta hoy a esta base de datos |
| Stockfish | Ejecutable externo | No se distribuye. Solo se lanza si se pide `--elo` y se indica `IDA_STOCKFISH_PATH` |

## Secretos

- `.env` está en `.gitignore`. El repositorio solo incluye `.env.example`, sin valores.
- Ningún componente necesita claves de API.

## Cómo avisar de un problema

Abre un *issue* en GitHub con el prefijo `[seguridad]` sin incluir detalles explotables, y se acordará un canal privado. Mientras el proyecto no tenga correo propio, GitHub Issues es la vía de contacto.
