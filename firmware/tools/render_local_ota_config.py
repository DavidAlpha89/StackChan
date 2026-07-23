#!/usr/bin/env python3
"""Render the untracked device-specific OTA defaults without printing secrets."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{32,128}\Z")
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "sdkconfig.defaults.local"


class ConfigRenderError(ValueError):
    """Raised when an unsafe or missing local firmware setting is supplied."""


def render(environment: Mapping[str, str], output: Path = DEFAULT_OUTPUT) -> Path:
    token = environment.get("STACKCHAN_BOOTSTRAP_TOKEN", "")
    if not TOKEN_PATTERN.fullmatch(token):
        raise ConfigRenderError(
            "STACKCHAN_BOOTSTRAP_TOKEN must be a 32-128 character URL-safe token"
        )
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "CONFIG_FORCE_CONFIG_OTA_URL=y\n"
        "CONFIG_FORCE_AI_AGENT_ON_BOOT=y\n"
        f'CONFIG_OTA_URL="http://192.168.50.200:9462/ota/{token}"\n'
    )
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{output.name}.",
            dir=output.parent,
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            os.chmod(temporary_name, 0o600)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, output)
        temporary_name = None
        output.chmod(0o600)
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    try:
        output = render(os.environ, arguments.output)
    except ConfigRenderError as exc:
        parser.error(str(exc))
    print(f"rendered private local defaults: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
