# Resumen conceptual de entrega

## Arquitectura

```text
Frontend ──┐
           ├── API ──→ Base de datos
Integración┘
```

La aplicación separa presentación, reglas de negocio e información
persistente. Los clientes consumen una interfaz común y no acceden
directamente a la base de datos.

## Entrega

```text
Repositorio → Validación → Artefacto → Registro → Entorno
```

El artefacto debe ser versionable, reproducible y promovido entre entornos sin
reconstruirlo con cambios ocultos.

## Infraestructura

- **Infraestructura como código:** describe el estado deseado.
- **Configuración:** instala y ajusta servicios de una máquina.
- **Observabilidad:** permite conocer el estado real del sistema.

## Seguridad

- Los secretos pertenecen al entorno de ejecución.
- Los valores públicos deben considerarse visibles.
- El mínimo privilegio limita el impacto de una falla.
- La rotación revoca material expuesto.

## Resultado esperado

Un sistema operable no es solo código funcionando: es código validado,
artefactos trazables, datos recuperables y señales claras de salud.
