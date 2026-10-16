# Ruta de arquitectura

## Vista general

```text
Usuarios
   ↓
Frontend ──→ API ──→ Persistencia
   │          │
   └──────→ Integraciones

Código ──→ CI/CD ──→ Infraestructura ──→ Observabilidad
```

## Capas

1. **Experiencia:** interfaz y clientes.
2. **Aplicación:** reglas de negocio y API.
3. **Datos:** persistencia, copias y recuperación.
4. **Entrega:** validación, empaquetado y promoción.
5. **Infraestructura:** recursos declarados y configuración.
6. **Observabilidad:** métricas, logs, trazas y alertas.

Cada capa debe tener límites claros, responsabilidades verificables y controles
de seguridad.
