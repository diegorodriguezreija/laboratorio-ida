# Líneas Base Tradicionales

Agentes convencionales simples, uno por mundo, contra los cuales comparar el diseño orgánico de IdA para que «mejora» signifique algo medible y reproducible.

## Agentes Disponibles

| Mundo | Agente | Tipo | Métrica de evaluación |
|---|---|---|---|
| **Snake** | `snake_bfs.py` | Búsqueda en anchura (BFS) pura con evasión de encierros (flood-fill) | Longitud alcanzada / latidos de vida |
| **Crafter** | *(Próximamente)* | Heurística voraz basada en necesidades vitales inmediatas | Logros desbloqueados / latidos de vida |
| **Ajedrez** | *(Próximamente)* | Minimax simple con evaluación de material básica | Tasa de victorias / longitud de partida |
| **Bosque** | *(Próximamente)* | Agente reflejo simple sin memoria ni deliberación | Tasa de supervivencia |
