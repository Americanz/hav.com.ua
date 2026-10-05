from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    token: str
    chat_id: str
    site_url: str
    port: int

    @classmethod
    def from_env(cls) -> Settings:
        site = os.environ.get("SITE_URL", "https://hav.com.ua").strip().rstrip("/")
        return cls(
            token=os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
            chat_id=os.environ.get("TELEGRAM_CHAT_ID", "").strip(),
            site_url=site or "https://hav.com.ua",
            port=int(os.environ.get("PORT", "8080")),
        )

    @property
    def configured(self) -> bool:
        return bool(self.token and self.chat_id)
