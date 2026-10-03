import asyncio
import logging
from collections.abc import Awaitable, Callable

from telegram import BotCommand, Update
from telegram.error import InvalidToken, TimedOut
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from .config import settings
from .database import (
    create_core_member,
    create_event,
    create_project,
    delete_core_member,
    delete_project,
    get_user_role,
    list_core_team,
    list_events,
    list_project_proposals,
    list_projects,
    list_speakers,
    promote_to_admin,
    register_attendee,
    update_core_member,
    update_project,
    upsert_user,
)


logger = logging.getLogger(__name__)
Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]


def sender_identity(update: Update) -> tuple[int, str | None, str]:
    """Extrae el identificador, usuario y nombre del remitente de Telegram."""
    user = update.effective_user
    if user is None:
        raise ValueError("No se pudo identificar al usuario de Telegram")
    return user.id, user.username, user.full_name


async def is_admin(telegram_id: int) -> bool:
    """Comprueba si el usuario es superusuario o tiene rol administrativo."""
    return telegram_id == settings.superuser_telegram_id or (
        await get_user_role(telegram_id)
    ) in {"admin", "superuser"}


async def require_admin(update: Update) -> int | None:
    """Verifica permisos administrativos y notifica el motivo si se deniegan."""
    if not update.message:
        return None
    try:
        telegram_id, _, _ = sender_identity(update)
    except ValueError as error:
        await update.message.reply_text(str(error))
        return None
    if not await is_admin(telegram_id):
        await update.message.reply_text("Este comando requiere permisos de admin.")
        return None
    return telegram_id


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando inicial con las instrucciones principales del bot."""
    if update.message:
        await update.message.reply_text(
            "Bienvenido. Usa /registrar Nombre Apellido para registrarte y ver tu nombre en la web oficial\n\n"
            "/eventos para consultar los eventos disponibles.\n\n"
        )


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra al usuario como asistente usando el nombre recibido."""
    if not update.message:
        return
    try:
        telegram_id, username, full_name = sender_identity(update)
    except ValueError as error:
        await update.message.reply_text(str(error))
        return

    display_name = " ".join(context.args).strip()
    if not display_name:
        await update.message.reply_text("Uso: /registrar Nombre Apellido")
        return

    await upsert_user(telegram_id, username, full_name)
    created, attendee = await register_attendee(telegram_id, display_name)
    if not created:
        assigned_name = attendee["display_name"] if attendee else display_name
        await update.message.reply_text(
            f"Ya tienes un cupo asignado con el nombre: {assigned_name}."
        )
        return
    await update.message.reply_text(f"Registro confirmado para {display_name}.")


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra al usuario los eventos disponibles y sus fechas."""
    if not update.message:
        return
    events = await list_events()
    if not events:
        await update.message.reply_text("No hay eventos disponibles.")
        return

    lines = [
        f"{event['id']}. {event['title']} | {event['event_date']}\n"
        f"{event['description']}"
        for event in events
    ]
    await update.message.reply_text("\n\n".join(lines))


async def create_event_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Crea un evento desde el formato de texto usado por el comando."""
    if not update.message:
        return
    try:
        telegram_id, username, full_name = sender_identity(update)
    except ValueError as error:
        await update.message.reply_text(str(error))
        return

    if not await is_admin(telegram_id):
        await update.message.reply_text("No tienes permisos para crear eventos.")
        return

    payload = " ".join(context.args)
    parts = [part.strip() for part in payload.split("|", maxsplit=2)]
    if len(parts) != 3 or not all(parts):
        await update.message.reply_text(
            "Uso: /crear_evento Título | YYYY-MM-DD | Descripción"
        )
        return

    await upsert_user(telegram_id, username, full_name)
    try:
        event_id = await create_event(
            title=parts[0],
            event_date=parts[1],
            description=parts[2],
            created_by=telegram_id,
        )
    except ValueError:
        await update.message.reply_text(
            "Fecha inválida. Usa exactamente YYYY-MM-DD, por ejemplo 2027-01-24."
        )
        return
    await update.message.reply_text(f"Evento creado correctamente con ID {event_id}.")


async def make_admin_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Promueve a administrador a otro usuario, solo desde el superusuario."""
    if not update.message:
        return
    try:
        telegram_id, _, _ = sender_identity(update)
    except ValueError as error:
        await update.message.reply_text(str(error))
        return

    if telegram_id != settings.superuser_telegram_id:
        await update.message.reply_text("Solo el superusuario puede hacer admins.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("Uso: /hacer_admin <telegram_id>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("El telegram_id debe ser numérico.")
        return

    await promote_to_admin(target_id)
    await update.message.reply_text(f"Usuario {target_id} promovido a admin.")


async def speakers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista los speakers registrados para los administradores."""
    if await require_admin(update) is None or not update.message:
        return
    speakers = await list_speakers()
    if not speakers:
        await update.message.reply_text("No hay speakers registrados.")
        return
    lines = [
        f"#{speaker['id']} {speaker['name']} | {speaker['company'] or 'Sin empresa'} | "
        f"{speaker['job_title'] or 'Sin cargo'}\n"
        f"Contacto: {speaker['email'] or '-'} / {speaker['phone'] or '-'}"
        for speaker in speakers
    ]
    await update.message.reply_text("\n\n".join(lines))


async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra una página de proyectos para consulta administrativa."""
    if await require_admin(update) is None or not update.message:
        return
    try:
        page = max(1, int(context.args[0])) if context.args else 1
    except ValueError:
        await update.message.reply_text("Uso: /proyectos [pagina]")
        return
    projects = await list_projects(page=page, page_size=5)
    if not projects:
        await update.message.reply_text(f"No hay proyectos en la página {page}.")
        return
    lines = [
        f"#{project['id']} {project['title']}\n"
        f"Encargado: {project['manager']} | Estado: {project['status']}\n"
        f"Repo: {project['repository_url']}\n"
        f"Landing: {project['landing_page_url'] or '-'}\n"
        f"{project['description']}"
        for project in projects
    ]
    footer = f"\n\nPágina {page}. Usa /proyectos {page + 1} para siguiente página."
    await update.message.reply_text("\n\n".join(lines) + footer)


async def project_proposals_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Muestra las propuestas de proyectos pendientes de revisión."""
    if await require_admin(update) is None or not update.message:
        return
    proposals = await list_project_proposals()
    if not proposals:
        await update.message.reply_text("No hay propuestas de proyectos registradas.")
        return
    lines = [
        f"#{proposal['id']} {proposal['name']}\n"
        f"Encargado: {proposal['manager']}\n"
        f"Contacto: {proposal['contact_email'] or '-'} / {proposal['contact_phone'] or '-'}\n"
        f"{proposal['description']}"
        for proposal in proposals
    ]
    await update.message.reply_text("\n\n".join(lines))


async def create_project_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Crea un proyecto a partir de sus campos separados por barras verticales."""
    if await require_admin(update) is None or not update.message:
        return
    parts = [part.strip() for part in " ".join(context.args).split("|",  maxsplit=5)]
    if len(parts) != 5 or not all(parts[:4]):
        await update.message.reply_text(
            "Uso: /crear_proyecto Título | Descripción | Encargado | Repo URL | Landing URL"
        )
        return
    project_id = await create_project(*parts[:4], parts[4] or None)
    await update.message.reply_text(f"Proyecto creado con ID #{project_id}.")


async def edit_project_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edita un proyecto aplicando los campos enviados por un administrador."""
    if await require_admin(update) is None or not update.message:
        return
    parts = [part.strip() for part in " ".join(context.args).split("|", maxsplit=6)]
    if len(parts) != 7:
        await update.message.reply_text(
            "Uso: /editar_proyecto ID | Título | Descripción | Encargado | Repo | Landing | Estado"
        )
        return
    try:
        project_id = int(parts[0])
    except ValueError:
        await update.message.reply_text("El ID debe ser numérico.")
        return
    updated = await update_project(project_id, dict(zip(
        ("title", "description", "manager", "repository_url", "landing_page_url", "status"),
        [*parts[1:]], strict=True,
    )))
    await update.message.reply_text("Proyecto actualizado." if updated else "Proyecto no encontrado.")


async def delete_project_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Elimina el proyecto identificado en el comando."""
    if await require_admin(update) is None or not update.message:
        return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Uso: /eliminar_proyecto ID")
        return
    deleted = await delete_project(int(context.args[0]))
    await update.message.reply_text("Proyecto eliminado." if deleted else "Proyecto no encontrado.")


async def core_team_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista los integrantes actuales del equipo principal."""
    if await require_admin(update) is None or not update.message:
        return
    members = await list_core_team()
    if not members:
        await update.message.reply_text("No hay miembros del core team.")
        return
    await update.message.reply_text("\n\n".join(
        f"#{member['id']} {member['name']} | {member['role']}\n"
        f"Instagram: {member['instagram'] or '-'} | LinkedIn: {member['linkedin'] or '-'} | GitHub: {member['github'] or '-'}"
        for member in members
    ))


async def create_core_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Añade un integrante del equipo con sus redes sociales opcionales."""
    if await require_admin(update) is None or not update.message:
        return
    parts = [part.strip() for part in " ".join(context.args).split("|", maxsplit=5)]
    if len(parts) < 3 or len(parts) > 6 or not all(parts[:3]):
        await update.message.reply_text(
            "Uso: /agregar_core Telegram ID | Nombre | Cargo | Instagram | LinkedIn | GitHub\n"
            "Instagram, LinkedIn y GitHub son opcionales."
        )
        return
    parts.extend([""] * (6 - len(parts)))
    try:
        telegram_id = int(parts[0])
    except ValueError:
        await update.message.reply_text("El Telegram ID debe ser numérico.")
        return
    member_id = await create_core_member(telegram_id, parts[1], parts[2], *[value or None for value in parts[3:]])
    await update.message.reply_text(f"Miembro de core team creado con ID #{member_id}.")


async def edit_core_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Actualiza un integrante del equipo con los campos proporcionados."""
    if await require_admin(update) is None or not update.message:
        return
    parts = [part.strip() for part in " ".join(context.args).split("|", maxsplit=6)]
    if len(parts) != 7:
        await update.message.reply_text("Uso: /editar_core ID | Telegram ID | Nombre | Cargo | Instagram | LinkedIn | GitHub")
        return
    try:
        member_id = int(parts[0])
        telegram_id = int(parts[1])
    except ValueError:
        await update.message.reply_text("Los IDs deben ser numéricos.")
        return
    updated = await update_core_member(member_id, {
        "telegram_id": telegram_id, "name": parts[2], "role": parts[3],
        "instagram": parts[4] or None, "linkedin": parts[5] or None, "github": parts[6] or None,
    })
    await update.message.reply_text("Miembro actualizado." if updated else "Miembro no encontrado.")


async def delete_core_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Elimina un integrante del equipo por su identificador."""
    if await require_admin(update) is None or not update.message:
        return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Uso: /eliminar_core ID")
        return
    deleted = await delete_core_member(int(context.args[0]))
    await update.message.reply_text("Miembro eliminado." if deleted else "Miembro no encontrado.")


async def telegram_error_handler(
    update: object, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Registra errores del bot y evita que una actualización lo detenga."""
    error = context.error
    if isinstance(error, TimedOut):
        logger.warning(
            "Telegram no respondió a tiempo. Comprueba la conexión de red o proxy."
        )
        return
    logger.error("Error procesando una actualización de Telegram", exc_info=error)


async def run_bot() -> None:
    """Construye el bot, registra comandos y mantiene el polling activo."""
    if not settings.bot_token:
        logger.warning("BOT_TOKEN no configurado; el bot no se iniciará.")
        return

    request = HTTPXRequest(
        connect_timeout=15.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=15.0,
    )
    updates_request = HTTPXRequest(
        connect_timeout=15.0,
        read_timeout=45.0,
        write_timeout=30.0,
        pool_timeout=15.0,
    )
    application = (
        Application.builder()
        .token(settings.bot_token)
        .request(request)
        .get_updates_request(updates_request)
        .build()
    )
    application.add_error_handler(telegram_error_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("registrar", register_command))
    application.add_handler(CommandHandler("eventos", events_command))
    application.add_handler(CommandHandler("crear_evento", create_event_command))
    application.add_handler(CommandHandler("hacer_admin", make_admin_command))
    application.add_handler(CommandHandler("speakers", speakers_command))
    application.add_handler(CommandHandler("proyectos", projects_command))
    application.add_handler(CommandHandler("propuestas", project_proposals_command))
    application.add_handler(CommandHandler("crear_proyecto", create_project_command))
    application.add_handler(CommandHandler("editar_proyecto", edit_project_command))
    application.add_handler(CommandHandler("eliminar_proyecto", delete_project_command))
    application.add_handler(CommandHandler("core_team", core_team_command))
    application.add_handler(CommandHandler("agregar_core", create_core_command))
    application.add_handler(CommandHandler("editar_core", edit_core_command))
    application.add_handler(CommandHandler("eliminar_core", delete_core_command))

    initialized = False
    started = False
    try:
        await application.initialize()
        initialized = True
        await application.bot.set_my_commands(
            [
                BotCommand("start", "Mostrar bienvenida y ayuda"),
                BotCommand("registrar", "Registrar nombre y apellido"),
                BotCommand("eventos", "Listar eventos disponibles"),
                BotCommand("crear_evento", "Crear un evento (admin)"),
                BotCommand("hacer_admin", "Promover usuario a admin"),
                BotCommand("speakers", "Ver speakers (admin)"),
                BotCommand("proyectos", "Listar proyectos (admin)"),
                BotCommand("propuestas", "Ver propuestas recibidas (admin)"),
                BotCommand("crear_proyecto", "Crear proyecto (admin)"),
                BotCommand("editar_proyecto", "Editar proyecto (admin)"),
                BotCommand("eliminar_proyecto", "Eliminar proyecto (admin)"),
                BotCommand("core_team", "Listar core team (admin)"),
                BotCommand("agregar_core", "Agregar core team (admin)"),
                BotCommand("editar_core", "Editar core team (admin)"),
                BotCommand("eliminar_core", "Eliminar core team (admin)"),
            ]
        )
        await application.start()
        started = True
        if application.updater is None:
            raise RuntimeError("El updater de Telegram no está disponible")
        await application.updater.start_polling()
        logger.info("Bot de Telegram iniciado")
        await asyncio.Event().wait()
    except InvalidToken:
        logger.error(
            "BOT_TOKEN rechazado por Telegram. Genera un token nuevo con "
            "@BotFather y actualiza .env."
        )
    finally:
        if application.updater and started:
            await application.updater.stop()
        if started:
            await application.stop()
        if initialized:
            await application.shutdown()


# Ejemplo independiente para practicar: responde al comando /hola.
async def hello_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Saluda a la persona que ejecuta el comando."""
    if update.message:
        user_name = update.effective_user.first_name if update.effective_user else "amigo"
        await update.message.reply_text(f"¡Hola, {user_name}! 👋")
