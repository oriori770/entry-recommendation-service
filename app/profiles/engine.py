from datetime import datetime
from typing import Dict, Any, Optional
from app.models.participant import Participant
from app.models.event import Event
from app.models.entry import Entry
from app.classification.time_buckets import get_time_bucket
from app.classification.temporal_features import get_day_of_week, is_arrival_on_time

class ProfileEngine:
    """
    Computes atomic MongoDB update operators for participant behavioral counters.
    """

    @staticmethod
    def build_atomic_entry_update(
        participant: Participant,
        event: Event,
        entry: Entry,
        streak_window_days: int = 7,
        punctuality_grace_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Builds the MongoDB atomic update document ($inc and $set) for an entry scan.
        """
        category_key = event.category or "other"
        time_bucket = event.time_bucket or get_time_bucket(entry.entryTime)
        day_of_week = get_day_of_week(entry.entryTime)
        on_time = is_arrival_on_time(entry.entryTime, event.date, punctuality_grace_minutes)

        # Streak calculation
        current_streak = participant.stats.streak.current_streak
        longest_streak = participant.stats.streak.longest_streak
        last_active = participant.stats.last_active

        if last_active is None:
            new_current_streak = 1
        else:
            delta_days = (entry.entryTime.date() - last_active.date()).days
            if 0 <= delta_days <= streak_window_days:
                new_current_streak = current_streak + 1
            else:
                new_current_streak = 1

        new_longest_streak = max(longest_streak, new_current_streak)

        punctuality_field = "stats.punctuality.on_time" if on_time else "stats.punctuality.late"

        update_doc = {
            "$inc": {
                f"stats.categories.{category_key}": 1,
                f"stats.time_buckets.{time_bucket}": 1,
                f"stats.days_of_week.{day_of_week}": 1,
                punctuality_field: 1,
                "stats.total_attendances": 1,
            },
            "$set": {
                "stats.last_active": entry.entryTime,
                "stats.streak.current_streak": new_current_streak,
                "stats.streak.longest_streak": new_longest_streak,
                "updatedAt": datetime.utcnow()
            }
        }
        return update_doc

    @staticmethod
    def apply_update_in_memory(participant: Participant, atomic_update: Dict[str, Any]) -> Participant:
        """
        Applies atomic update in-memory to a Participant model (useful for unit tests & simulations).
        """
        inc_ops = atomic_update.get("$inc", {})
        set_ops = atomic_update.get("$set", {})

        stats = participant.stats

        for path, val in inc_ops.items():
            if path.startswith("stats.categories."):
                cat = path.split(".")[-1]
                stats.categories[cat] = stats.categories.get(cat, 0) + val
            elif path.startswith("stats.time_buckets."):
                tb = path.split(".")[-1]
                stats.time_buckets[tb] = stats.time_buckets.get(tb, 0) + val
            elif path.startswith("stats.days_of_week."):
                dow = path.split(".")[-1]
                stats.days_of_week[dow] = stats.days_of_week.get(dow, 0) + val
            elif path == "stats.punctuality.on_time":
                stats.punctuality.on_time += val
            elif path == "stats.punctuality.late":
                stats.punctuality.late += val
            elif path == "stats.total_attendances":
                stats.total_attendances += val

        if "stats.last_active" in set_ops:
            stats.last_active = set_ops["stats.last_active"]
        if "stats.streak.current_streak" in set_ops:
            stats.streak.current_streak = set_ops["stats.streak.current_streak"]
        if "stats.streak.longest_streak" in set_ops:
            stats.streak.longest_streak = set_ops["stats.streak.longest_streak"]

        return participant
