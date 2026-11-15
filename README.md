# Semaforos-CABA

Sistema de análisis y simulación para estudiar posibles mejoras en los tiempos de los semáforos y la circulación vehicular en la Ciudad de Buenos Aires.

## Objetivo

Evaluar, mediante un gemelo digital en [SUMO](https://eclipse.dev/sumo/) calibrado con datos reales de CABA, si adaptar los tiempos de los semáforos a cada franja horaria (con métodos clásicos y con aprendizaje por refuerzo) reduce demoras y colas frente al plan actual, en un corredor piloto de 5 a 10 cruces.

No se tocan semáforos reales: todo se prueba en simulación.

## Documentación

| Documento | Contenido |
|---|---|
| [AGENTS.md](AGENTS.md) | Contexto del proyecto, estructura del repo, reglas de trabajo y advertencias sobre los datos. Lo leen los agentes de IA y sirve de resumen para cualquiera |
| [docs/datos/](docs/datos/README.md) | Catálogo de fuentes de datos, garantías de cada una y cómo actualizarlas |

## Datos incluidos

- `data/cruces-semaforizados/`: ubicación de los cruces semaforizados de CABA (BA Data, CC-BY-2.5-AR), como dataset de prueba.
- El GTFS de colectivos no se versiona por tamaño; ver [docs/datos/gtfs-colectivos.md](docs/datos/gtfs-colectivos.md).

## Usar agentes de IA en este repo

El repo tiene un [AGENTS.md](AGENTS.md) que Codex, Cursor, Copilot y otros agentes leen solos. Para Claude Code, `CLAUDE.md` lo importa. Si encontrás algo que el agente hace mal por falta de contexto (un dato mal interpretado, una regla que no conoce), agregalo al `AGENTS.md` en un PR.
