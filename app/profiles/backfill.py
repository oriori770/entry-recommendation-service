from typing import List, Dict, Optional
from datetime import datetime
from app.models.participant import Participant
from app.models.event import Event
from app.models.entry import Entry
from app.classification.service import EventClassificationService
from app.profiles.engine import ProfileEngine

class BackfillService:
    """
    Processes historical entry scans in chronological order to build
    accurate cumulative behavioral stats for participants.
    """

    def __init__(self, classification_service: EventClassificationService, db=None):
        self.classification_service = classification_service
        self.db = db

    async def replay_participant_entries(
        self,
        participant: Participant,
        entries: List[Entry],
        events_by_id: Dict[str, Event],
        group_id: Optional[str] = None
    ) -> Participant:
        """
        Replays sorted historical entries for a single participant.
        """
        # Sort entries chronologically
        sorted_entries = sorted(entries, key=lambda e: e.entryTime)

        for entry in sorted_entries:
            event = events_by_id.get(str(entry.eventId))
            if not event:
                continue

            # Ensure event has category
            if not event.category:
                res = await self.classification_service.get_or_classify_event(event, group_id=group_id)
                event.category = res.category_key

            # Generate and apply atomic update
            update_op = ProfileEngine.build_atomic_entry_update(participant, event, entry)
            ProfileEngine.apply_update_in_memory(participant, update_op)

        return participant

    async def backfill_all_participants(self, group_id: Optional[str] = None) -> int:
        """
        Replays all entries in the MongoDB database and updates participant stats.
        """
        if self.db is None:
            return 0

        # 1. Fetch all events and classify them if needed
        events_cursor = self.db["events"].find({})
        events_by_id = {}
        async for doc in events_cursor:
            ev = Event.model_validate(doc)
            if not ev.category:
                res = await self.classification_service.get_or_classify_event(ev, group_id=group_id)
                ev.category = res.category_key
            events_by_id[str(ev.id)] = ev

        # 2. Fetch all entries
        entries_cursor = self.db["entries"].find({}).sort("entryTime", 1)
        entries_by_participant: Dict[str, List[Entry]] = {}
        async for doc in entries_cursor:
            entry = Entry.model_validate(doc)
            p_id = str(entry.participantId)
            if p_id not in entries_by_participant:
                entries_by_participant[p_id] = []
            entries_by_participant[p_id].append(entry)

        # 3. Process each participant
        updated_count = 0
        for p_id, p_entries in entries_by_participant.items():
            p_doc = await self.db["participants"].find_one({"_id": p_entries[0].participantId})
            if not p_doc:
                continue
            participant = Participant.model_validate(p_doc)
            # Reset stats before replaying
            participant.stats = participant.stats.__class__()

            updated_p = await self.replay_participant_entries(
                participant, p_entries, events_by_id, group_id=group_id
            )

            # Persist to MongoDB
            await self.db["participants"].update_one(
                {"_id": updated_p.id},
                {"$set": {"stats": updated_p.stats.model_dump()}}
            )
            updated_count += 1

        return updated_count
