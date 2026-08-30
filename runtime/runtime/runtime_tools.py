from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from .mmr import select_mmr


class KernelInterface(Protocol):
    def record(
        self,
        project_id: str,
        record_type: str,
        content: dict[str, Any],
        artifact_ids: tuple[str, ...] = (),
    ) -> object: ...

    def connect(
        self,
        project_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
    ) -> object: ...

    def remove_record(self, project_id: str, record_id: str) -> None: ...

    def remove_relation(self, project_id: str, relation_id: str) -> None: ...

    def local_map(self, project_id: str, query: object) -> object: ...


class RuntimeTools:
    def __init__(
        self, kernel: KernelInterface | None, selected: list[str] | tuple[str, ...] = ()
    ):
        self._kernel = kernel
        self._selected = frozenset(selected)

    def invoke(self, tool_id: str, operation: str, values: Mapping[str, Any]):
        if tool_id not in self._selected:
            raise KeyError(f"tool is not selected: {tool_id}")
        if tool_id == "kernel":
            return self._invoke_kernel(operation, values)
        if tool_id == "brainstorm":
            return self._invoke_brainstorm(operation, values)
        raise KeyError(f"unknown tool operation: {tool_id}.{operation}")

    def _invoke_kernel(self, operation, values):
        if self._kernel is None:
            raise RuntimeError("kernel tool requires a KernelInterface")
        handlers = {
            "record": self._record,
            "connect": self._connect,
            "remove_record": self._remove_record,
            "remove_relation": self._remove_relation,
            "local_map": self._local_map,
        }
        try:
            return handlers[operation](values)
        except KeyError as error:
            if error.args == (operation,):
                raise KeyError(f"unknown tool operation: kernel.{operation}") from None
            raise

    def _invoke_brainstorm(self, operation, values):
        if operation != "mmr":
            raise KeyError(f"unknown tool operation: brainstorm.{operation}")
        return select_mmr(values)

    def _record(self, values: Mapping[str, Any]):
        return self._kernel.record(
            values["project_id"],
            values["record_type"],
            values["content"],
            tuple(values.get("artifact_ids", ())),
        )

    def _connect(self, values):
        return self._kernel.connect(
            values["project_id"],
            values["source_id"],
            values["target_id"],
            values["relation_type"],
        )

    def _remove_record(self, values):
        return self._kernel.remove_record(values["project_id"], values["record_id"])

    def _remove_relation(self, values):
        return self._kernel.remove_relation(
            values["project_id"], values["relation_id"]
        )

    def _local_map(self, values):
        return self._kernel.local_map(values["project_id"], values["query"])
