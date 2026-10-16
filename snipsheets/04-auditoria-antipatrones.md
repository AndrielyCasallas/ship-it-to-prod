# Antipatrones de entrega

| Antipatrón | Riesgo | Principio correctivo |
|---|---|---|
| Secreto dentro de una imagen | Exposición persistente | Inyección en runtime y rotación |
| Datos dentro del contenedor | Pérdida al reemplazarlo | Almacenamiento externo |
| Imagen mutable | Resultados distintos | Versiones inmutables |
| Sin healthcheck | Fallas invisibles | Señales de salud |
| Despliegue manual | Errores no repetibles | Automatización revisable |
| Privilegios excesivos | Mayor impacto de una intrusión | Mínimo privilegio |

## Regla

Un sistema seguro reduce la cantidad de decisiones manuales y hace visibles
sus fallas.
