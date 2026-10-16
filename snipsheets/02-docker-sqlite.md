# Contenedores y persistencia

## Flujo conceptual

```text
Código fuente → Imagen inmutable → Contenedor → Servicio
                                      ↓
                                  Volumen de datos
```

## Contenedores

- Aíslan procesos y dependencias.
- Hacen explícito el entorno de ejecución.
- Deben ser pequeños, reproducibles y ejecutarse con el menor privilegio.
- No deben contener secretos ni datos permanentes.

## Persistencia

Un contenedor puede reemplazarse. Los datos deben vivir en un volumen o en un
servicio de almacenamiento adecuado al nivel de disponibilidad requerido.

SQLite es útil para aplicaciones pequeñas y despliegues simples; su elección
debe considerar concurrencia, copias de seguridad y crecimiento.
