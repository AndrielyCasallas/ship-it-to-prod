# CI/CD: conceptos

## Pipeline

```text
Cambio → Revisión → Tests → Build → Registro → Despliegue → Verificación
```

## CI

La integración continua valida cambios pequeños con compilación, análisis y
tests automatizados.

## CD

La entrega continua mantiene un artefacto listo para publicar. El despliegue
continuo agrega la publicación automática bajo controles y aprobaciones.

## Principios

- Construir una vez y promover el mismo artefacto.
- Separar permisos de lectura, publicación y despliegue.
- No imprimir secretos en logs.
- Mantener trazabilidad entre cambio, artefacto y entorno.
