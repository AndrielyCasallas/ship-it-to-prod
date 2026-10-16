# Configuración opcional con Ansible

Esta carpeta contiene un playbook público para configurar Docker y desplegar
un stack mínimo de observabilidad en un host Alpine. Es un complemento
opcional de Terraform; la aplicación funciona localmente sin esta carpeta.

## Requisitos y restricciones

- El equipo de control debe usar **Linux o macOS**.
- Windows no está soportado como entorno de control nativo; usa WSL2 o una
  máquina Linux/macOS si necesitas ejecutar el playbook.
- El host remoto debe ser un sistema Linux compatible con los comandos de
  Alpine usados por el playbook.
- Se requiere Ansible, acceso SSH, Docker y Docker Compose en el host remoto.
- La cuenta remota necesita permisos suficientes para instalar paquetes,
  iniciar servicios y crear contenedores.
- El equipo de control debe tener conectividad de red hacia SSH y el host debe
  poder descargar paquetes e imágenes.
- No se incluyen inventarios, claves, usuarios ni direcciones de red porque
  dependen de cada entorno.

El playbook no configura Windows, macOS como host remoto ni otros sistemas que
no proporcionen los comandos y servicios esperados. La compatibilidad indicada
para macOS corresponde únicamente al equipo desde el que se ejecuta Ansible.

## Flujo

```text
Terraform crea el host → Ansible configura Docker → Observabilidad publica métricas
```

El playbook espera conectividad SSH, instala Docker, inicia el servicio y
publica el Compose de observabilidad definido en
`roles/observability/templates/docker-compose.yml.j2`.

## Uso local

El inventario no se incluye porque depende de cada entorno. Crea uno local y
mantén fuera de Git las direcciones privadas, usuarios, claves e inventarios.
Después valida la sintaxis y ejecuta el playbook desde la raíz del proyecto.

```text
ansible-playbook --syntax-check ansible/site.yml
ansible-playbook -i <inventario-local> ansible/site.yml
```

No guardes credenciales ni claves privadas en esta carpeta. El playbook usa
imágenes públicas como ejemplo; en un entorno real conviene fijar versiones,
restringir puertos y revisar los permisos de los contenedores de observabilidad.

## Consideraciones de seguridad

Este ejemplo publica los puertos de las métricas y utiliza un contenedor de
observabilidad con permisos elevados para inspeccionar Docker. No lo expongas
directamente a Internet. En un entorno real debes fijar versiones de imágenes,
restringir la red, proteger el acceso a métricas, revisar privilegios y definir
retención y autenticación.

## Alcance

Este ejemplo no configura una plataforma completa de monitoreo: solo muestra
la relación entre automatización de configuración, Docker y métricas. Ajusta
la red, almacenamiento, autenticación y retención antes de usarlo en un
entorno real.
