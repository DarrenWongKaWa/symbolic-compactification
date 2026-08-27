"""Frozen DeepSeek proposer config. Do not tune on TEST."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

PROTOCOL_ID = "deepseek-abstraction-protocol-v1-dev"
CONFIG_ID = "deepseek-v4-pro-thinking-high-v1"
PRIMARY_MODEL = "deepseek-v4-pro"
FLASH_MODEL = "deepseek-v4-flash"
BASE_URL = "https://api.deepseek.com"

# Thinking mode ignores temperature/top_p (DeepSeek docs). Omit them.
# json_object is format control, not scientific repair.
FROZEN = {
    "model": PRIMARY_MODEL,
    "reasoning_effort": "high",
    "thinking": {"type": "enabled"},
    "max_tokens": 16384,
    "timeout_s": 180.0,
    "retries_network": 1,
    "retries_parse": 0,  # never retry to "fix" scientific content
    "response_format": {"type": "json_object"},
    "temperature": None,  # unsupported / ignored in thinking mode
    "top_p": None,
    "n_hypotheses_max": 5,
    "packet_cap_default": 10,
    "seed_flagship": 5,
    "seed_secondary": 3,
    "sol_backends": "relations",
    "sol_timeout_s": 12.0,
    "sol_timeout_guo_s": 180.0,
}


@dataclass
class ProposerConfig:
    model: str = PRIMARY_MODEL
    reasoning_effort: str = "high"
    thinking_type: str = "enabled"
    max_tokens: int = 16384
    timeout_s: float = 180.0
    retries_network: int = 1
    condition: str = "A0"  # A0 raw | A1 summary | A2 raw+SOL | A3 SOL-only
    packet_cap: int = 10
    n_hypotheses_max: int = 5
    sol_backends: str = "relations"
    sol_timeout_s: float = 12.0
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["config_id"] = CONFIG_ID
        d["protocol_id"] = PROTOCOL_ID
        d["temperature"] = None
        d["response_format"] = "json_object"
        return d


def primary_config(**kwargs) -> ProposerConfig:
    return ProposerConfig(**kwargs)


def flash_config(**kwargs) -> ProposerConfig:
    kwargs.setdefault("model", FLASH_MODEL)
    return ProposerConfig(**kwargs)
