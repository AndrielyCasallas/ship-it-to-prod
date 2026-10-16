# Persistencia: conceptos

## Ciclo de vida

```text
Servicio inicia → Lee datos persistentes → Procesa cambios
                                         ↓
                              Escribe en almacenamiento
```

## Diferencias

- **Imagen:** artefacto inmutable de la aplicación.
- **Contenedor:** instancia temporal de la imagen.
- **Volumen:** datos que sobreviven al reemplazo del contenedor.
- **Backup:** copia recuperable, independiente del volumen original.

## Preguntas de diseño

- ¿Qué datos se pueden perder?
- ¿Cómo se recuperan?
- ¿Quién puede leerlos o modificarlos?
- ¿Cómo se comprueba que una copia funciona?
