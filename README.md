# Semaforos-CABA
Sistema de análisis y simulación para estudiar posibles mejoras en los tiempos de los semáforos y la circulación vehicular en la Ciudad de Buenos Aires.

## Cómo empezar

1. Instalar el entorno (Windows, Linux o WSL): [docs/setup-sumo.md](docs/setup-sumo.md)
2. Correr la demo: `python scripts/run_sumo_rl_demo.py --scenario santa-fe-coronel-diaz`
3. Ver el escenario: `sumo-gui -c scenarios/santa-fe-coronel-diaz/cruce.sumocfg`

## Contenido

| Ruta | Qué hay |
|---|---|
| `scenarios/` | Escenarios de SUMO (red + demanda). Ver [scenarios/README.md](scenarios/README.md) |
| `scripts/run_sumo_rl_demo.py` | Plan fijo vs. Q-learning (SUMO-RL) sobre un escenario |
| `scripts/build_scenario.py` | **Regenera un escenario desde OpenStreetMap.** Usarlo para crear o reconstruir cruces |
| `scripts/tls_template.py` | Genera la plantilla para cargar tiempos reales de un semáforo |
| `docs/setup-sumo.md` | Instalación y problemas conocidos |
| `docs/integracion.md` | Cómo se conectan los datos de las otras tareas con la simulación |

## Estado

Entorno de simulación funcionando. Los tiempos de semáforo y la demanda del cruce de prueba son valores por defecto, no datos reales de la Ciudad.
