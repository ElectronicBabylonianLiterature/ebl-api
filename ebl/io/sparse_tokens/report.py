import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CollectionReport:
    collection: str
    scanned: int = 0
    unchanged: int = 0
    changed: int = 0
    written: int = 0
    bytes_before: int = 0
    bytes_after: int = 0
    unreadable: Dict[str, str] = field(default_factory=dict)
    lossy: List[str] = field(default_factory=list)
    dropped_keys: Dict[str, List[str]] = field(default_factory=dict)
    oversized: Dict[str, int] = field(default_factory=dict)
    failed: Dict[str, str] = field(default_factory=dict)
    not_found: int = 0
    interrupted: Optional[str] = None

    @property
    def has_problems(self) -> bool:
        problems = (
            self.unreadable,
            self.lossy,
            self.dropped_keys,
            self.oversized,
            self.failed,
            self.not_found,
            self.interrupted,
        )
        return any(problems)

    def log(self, apply: bool) -> None:
        logger.info(
            "%s: %d scanned, %d already sparse, %d %s, %d written; "
            "changed documents %d -> %d bytes",
            self.collection,
            self.scanned,
            self.unchanged,
            self.changed,
            "to write" if apply else "would be rewritten",
            self.written,
            self.bytes_before,
            self.bytes_after,
        )
        self._log_run_problems()
        for label, problems in (
            ("could not be read", self.unreadable),
            ("are not lossless and were left alone", self.lossy),
            ("would lose token keys and were left alone", self.dropped_keys),
            ("would exceed the document size limit", self.oversized),
            ("could not be written", self.failed),
        ):
            if problems:
                logger.error(
                    "%s: %d documents %s", self.collection, len(problems), label
                )
                for item in (
                    problems if isinstance(problems, list) else problems.items()
                ):
                    logger.error("  %s", item)

    def _log_run_problems(self) -> None:
        if self.interrupted:
            logger.error(
                "%s: scan stopped early: %s", self.collection, self.interrupted
            )
        if self.not_found:
            logger.error(
                "%s: %d updates matched no document (deleted during the run?)",
                self.collection,
                self.not_found,
            )
