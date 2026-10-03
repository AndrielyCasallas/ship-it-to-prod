# Path permite trabajar con rutas de archivos de forma independiente del sistema
# operativo.
from pathlib import Path

# Field define valores predeterminados y permite indicar el nombre de la
# variable de entorno que alimenta cada atributo.
from pydantic import Field
# BaseSettings lee y valida la configuración; SettingsConfigDict indica cómo
# debe buscarla, por ejemplo, dentro de un archivo .env.
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Credenciales y permisos del bot de Telegram.
    bot_token: str = Field(default="", validation_alias="BOT_TOKEN")
    superuser_telegram_id: int = Field(default=0, validation_alias="SUPERUSER_TELEGRAM_ID")

    # URL de la base de datos que utiliza el backend.
    database_url: str = Field(
        default="sqlite:///./community.db",
        validation_alias="DATABASE_URL",
    )

    # Dirección y puerto donde se inicia la API.
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")

    # Clave que protege los endpoints que requieren autenticación.
    api_key: str = Field(default="", validation_alias="API_KEY")

    # Orígenes permitidos para las peticiones del frontend (configuración CORS).
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:5173",
        validation_alias="CORS_ORIGINS",
    )

    # Configuración de carga de variables de entorno.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_path(self) -> Path:
        """Convierte la URL SQLite configurada en una ruta utilizable.

        Returns:
            Path: Ruta relativa o absoluta sin el prefijo ``sqlite:///``.

        Raises:
            ValueError: Si la URL configurada no corresponde al formato
                SQLite admitido por la aplicación.
        """
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            raise ValueError("DATABASE_URL debe usar el formato sqlite:///ruta.db")
        # Se elimina el prefijo de conexión para obtener únicamente la ruta
        # que puede utilizarse con operaciones normales de archivos.
        return Path(self.database_url.removeprefix(prefix))


# Instancia única de configuración reutilizada por el resto de la aplicación.
settings = Settings()
