"""JSON 存档仓储。"""
from __future__ import annotations

import json
from pathlib import Path

from ..snapshot import GameSnapshot


class SaveLoadError(RuntimeError):
    """存读档异常。"""


class JsonSaveRepository:
    """负责将快照写入和读取 JSON 文件。"""

    def save(self, filename: str, snapshot: GameSnapshot) -> None:
        path = Path(filename)
        with path.open("w", encoding="utf-8") as file:
            json.dump(snapshot.to_dict(), file, ensure_ascii=False, indent=2)

    def load(self, filename: str) -> GameSnapshot:
        path = Path(filename)

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as exc:
            raise SaveLoadError(f"存档文件 {filename} 不存在。") from exc
        except json.JSONDecodeError as exc:
            raise SaveLoadError(f"存档文件 {filename} 的 JSON 格式损坏。") from exc

        if not isinstance(data, dict):
            raise SaveLoadError("存档结构不正确。")

        try:
            return GameSnapshot.from_dict(data)
        except (KeyError, TypeError, ValueError) as exc:
            raise SaveLoadError(f"存档结构不正确：{exc}") from exc