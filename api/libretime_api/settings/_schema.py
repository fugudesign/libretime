from typing import List, Literal, Optional

from libretime_shared.config import (
    BaseConfig,
    DatabaseConfig,
    GeneralConfig,
    RabbitMQConfig,
    StationConfig,
    StorageConfig,
)
from pydantic import BaseModel


class EmailConfig(BaseModel):
    from_email: str = "no-reply@libretime.org"

    host: str = "localhost"
    port: int = 25
    user: str = ""
    password: str = ""
    encryption: Optional[Literal["ssl/tls", "starttls"]] = None
    timeout: Optional[int] = None
    key_file: Optional[str] = None
    cert_file: Optional[str] = None


class Config(BaseConfig):
    general: GeneralConfig
    database: DatabaseConfig = DatabaseConfig()
    rabbitmq: RabbitMQConfig = RabbitMQConfig()
    storage: StorageConfig = StorageConfig()
    stations: List[StationConfig] = [StationConfig(id=1, name="Default")]
    email: EmailConfig = EmailConfig()
