# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic offline result used by the portable runtime smoke test."""

import typing as t

from searx.result_types import EngineResults, MainResult
from searx.enginelib import EngineAbout

if t.TYPE_CHECKING:
    from searx.search.processors import RequestParams


engine_type = "offline"
categories = ["general"]
disabled = False
timeout = 2.0
language = "en"
about = EngineAbout(
    results="JSON",
    description="Deterministic NexusSearch portable runtime smoke engine.",
)


def init(engine_settings: dict[str, t.Any]) -> bool:  # pylint: disable=unused-argument
    """Initialize the deterministic engine without external services."""
    return True


def search(query: str, params: "RequestParams") -> EngineResults:  # pylint: disable=unused-argument
    """Return one stable result while ignoring external search services."""
    results = EngineResults()
    results.add(
        MainResult(
            title="NexusSearch deterministic result",
            url="https://example.invalid/nexussearch-smoke",
            content=f"Deterministic search result for {query}.",
            engine="nexussearch demo",
        )
    )
    return results
