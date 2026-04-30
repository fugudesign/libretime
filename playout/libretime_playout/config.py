from pathlib import Path
from typing import List, Literal, Optional

from libretime_shared.config import (
    BaseConfig,
    GeneralConfig,
    RabbitMQConfig,
    StationConfig,
    StreamConfig,
)
from pydantic import BaseModel, model_validator

CACHE_DIR = Path.cwd() / "scheduler"
RECORD_DIR = Path.cwd() / "recorder"

PUSH_INTERVAL: float = 2.0
POLL_INTERVAL: float = 400.0


class PlayoutConfig(BaseModel):
    liquidsoap_host: str = "localhost"
    liquidsoap_port: int = 1234

    record_file_format: Literal["mp3", "ogg"] = "ogg"  # record_file_type
    record_bitrate: int = 256
    record_samplerate: int = 44100
    record_channels: int = 2
    record_sample_size: int = 16


class LiquidsoapConfig(BaseModel):
    server_listen_address: str = "127.0.0.1"
    server_listen_port: int = 1234

    harbor_listen_address: List[str] = ["0.0.0.0"]

    harbor_ssl_certificate: Optional[str] = None
    harbor_ssl_private_key: Optional[str] = None
    harbor_ssl_password: Optional[str] = None

    @model_validator(mode="after")
    def _validate_harbor_ssl(self):
        if (
            self.harbor_ssl_certificate is not None
            and self.harbor_ssl_private_key is None
        ):
            raise ValueError("missing 'harbor_ssl_private_key' value")

        if (
            self.harbor_ssl_certificate is None
            and self.harbor_ssl_private_key is not None
        ):
            raise ValueError("missing 'harbor_ssl_certificate' value")

        return self


class Config(BaseConfig):
    general: GeneralConfig
    rabbitmq: RabbitMQConfig = RabbitMQConfig()
    playout: PlayoutConfig = PlayoutConfig()
    liquidsoap: LiquidsoapConfig = LiquidsoapConfig()
    stream: Optional[StreamConfig] = None   # kept for backward compatibility
    stations: List[StationConfig] = []

    @model_validator(mode="after")
    def _normalize_stations(self) -> "Config":
        """If no stations are defined but a legacy stream block exists, wrap it as station id=1."""
        if not self.stations and self.stream is not None:
            self.stations = [StationConfig(id=1, name="Default", stream=self.stream)]
        return self
