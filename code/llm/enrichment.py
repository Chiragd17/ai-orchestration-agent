"""
llm/enrichment.py — Real apply_image_amounts and apply_message_effects using Groq.

Replaces the Phase 2 stubs in reconcile.py with actual LLM-backed extraction.
Called before reconcile.resolve() so that the real amounts/effects are baked in.
"""

import copy
import os
from decimal import Decimal
from pathlib import Path
from typing import List

import pandas as pd

from engine.data.state import Event
from llm.client import extract_image_amount, classify_message


def _get_dataset_root() -> Path:
    """Resolve dataset/ relative to project root."""
    here = Path(__file__).parent
    return here.parent.parent / "dataset"


def apply_image_amounts(events: List[Event], images_df: pd.DataFrame) -> List[Event]:
    """
    For every event in `events` that has amount=None AND appears in images_df,
    call extract_image_amount() to fill the missing amount.
    Returns a new list — never mutates the originals.
    """
    dataset_root = _get_dataset_root()
    images_dir = dataset_root / "media" / "images"

    # Build a map: event_id -> image_id
    event_to_image = {}
    for _, row in images_df.iterrows():
        ev_id = row.get("related_event_id")
        img_id = row.get("image_id")
        if ev_id and img_id:
            event_to_image[str(ev_id).strip()] = str(img_id).strip()

    out = []
    for e in events:
        new_e = copy.deepcopy(e)
        if new_e.amount is None and new_e.event_id in event_to_image:
            image_id = event_to_image[new_e.event_id]
            image_path = images_dir / f"{image_id}.png"
            if image_path.exists():
                extracted = extract_image_amount(str(image_path), image_id)
                if extracted is not None:
                    new_e.amount = extracted
        out.append(new_e)
    return out


def apply_message_effects(
    events: List[Event],
    messages_df: pd.DataFrame,
    request_id: str,
) -> List[Event]:
    """
    For every message in messages_df that belongs to this request (or is user-level),
    classify it with classify_message() and apply its effect to the relevant event.

    Effects applied:
      confirm  -> event.status = 'confirmed' (already settled, no change needed)
      amend    -> update event.amount and/or event.date
      cancel   -> event.status = 'cancelled'
      delay    -> update event.date to new_date if provided
      irrelevant -> no change

    Returns a new list — never mutates the originals.
    """
    event_map = {e.event_id: copy.deepcopy(e) for e in events}

    # Filter messages relevant to this request
    relevant_messages = messages_df[
        (messages_df["request_id"] == request_id) |
        (messages_df["request_id"].isna()) |
        (messages_df["request_id"] == "")
    ]

    for _, row in relevant_messages.iterrows():
        message_id = str(row["message_id"]).strip()
        message_text = str(row["message_text"]).strip() if pd.notna(row["message_text"]) else ""
        related_event_id = str(row["related_event_id"]).strip() if pd.notna(row["related_event_id"]) else ""

        if not message_text:
            continue

        # Build context string about the related event (if known)
        event_context = ""
        if related_event_id and related_event_id in event_map:
            ev = event_map[related_event_id]
            event_context = (
                f"Event: {ev.description}, "
                f"Amount: {ev.amount}, "
                f"Status: {ev.status}, "
                f"Date: {ev.date}"
            )

        result = classify_message(message_text, message_id, event_context)
        effect = result.get("effect", "irrelevant")
        new_amount = result.get("new_amount")
        new_date = result.get("new_date")

        if related_event_id and related_event_id in event_map:
            ev = event_map[related_event_id]
            if effect == "amend":
                if new_amount is not None:
                    ev.amount = Decimal(str(new_amount))
                if new_date is not None:
                    ev.date = new_date
            elif effect == "cancel":
                ev.status = "cancelled"
            elif effect == "delay":
                if new_date is not None:
                    ev.date = new_date
            elif effect == "confirm":
                pass  # Already settled — no mutation needed
            # irrelevant: no change

    return list(event_map.values())
