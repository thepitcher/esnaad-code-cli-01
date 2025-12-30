"""User preference learning and storage."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
from pydantic import BaseModel, Field

from esnaad.config.settings import get_settings


class Preference(BaseModel):
    """A single learned preference."""

    key: str = Field(description="Preference key/name")
    value: Any = Field(description="Preference value")
    source: str = Field(description="Where this preference was learned from")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence level (0-1)",
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    access_count: int = Field(default=0, description="Times this preference was accessed")


class PreferenceCategory(BaseModel):
    """Category of preferences."""

    name: str = Field(description="Category name")
    preferences: dict[str, Preference] = Field(default_factory=dict)


class UserPreferences(BaseModel):
    """User preferences storage."""

    version: int = Field(default=1, description="Schema version")
    categories: dict[str, PreferenceCategory] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)


class PreferenceManager:
    """
    Manages user preferences learned from interactions.

    Stores preferences in a JSON file and provides methods
    to learn from clarification responses, retrieve preferences,
    and suggest values for future questions.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        """
        Initialize the preference manager.

        Args:
            config_dir: Directory for storing preferences
        """
        if config_dir is None:
            settings = get_settings()
            config_dir = settings.config_dir

        self.config_dir = config_dir
        self.prefs_file = config_dir / "preferences.json"
        self._preferences: UserPreferences | None = None

    async def load(self) -> UserPreferences:
        """Load preferences from disk."""
        if self._preferences is not None:
            return self._preferences

        if self.prefs_file.exists():
            try:
                async with aiofiles.open(self.prefs_file, "r") as f:
                    data = json.loads(await f.read())
                    self._preferences = UserPreferences.model_validate(data)
            except (json.JSONDecodeError, ValueError):
                # Invalid file, start fresh
                self._preferences = UserPreferences()
        else:
            self._preferences = UserPreferences()

        return self._preferences

    async def save(self) -> None:
        """Save preferences to disk."""
        if self._preferences is None:
            return

        self._preferences.last_updated = datetime.now()

        # Ensure directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(self.prefs_file, "w") as f:
            data = self._preferences.model_dump(mode="json")
            await f.write(json.dumps(data, indent=2, default=str))

    async def set_preference(
        self,
        category: str,
        key: str,
        value: Any,
        source: str = "user",
        confidence: float = 1.0,
    ) -> None:
        """
        Set a preference value.

        Args:
            category: Category name (e.g., "coding_style", "tools")
            key: Preference key
            value: Preference value
            source: Where this preference came from
            confidence: Confidence level (0-1)
        """
        prefs = await self.load()

        # Ensure category exists
        if category not in prefs.categories:
            prefs.categories[category] = PreferenceCategory(name=category)

        cat = prefs.categories[category]

        # Update or create preference
        if key in cat.preferences:
            pref = cat.preferences[key]
            pref.value = value
            pref.updated_at = datetime.now()
            # Increase confidence if consistent
            if pref.value == value:
                pref.confidence = min(1.0, pref.confidence + 0.1)
        else:
            cat.preferences[key] = Preference(
                key=key,
                value=value,
                source=source,
                confidence=confidence,
            )

        await self.save()

    async def get_preference(
        self,
        category: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get a preference value.

        Args:
            category: Category name
            key: Preference key
            default: Default value if not found

        Returns:
            Preference value or default
        """
        prefs = await self.load()

        if category not in prefs.categories:
            return default

        cat = prefs.categories[category]
        if key not in cat.preferences:
            return default

        pref = cat.preferences[key]
        pref.access_count += 1
        return pref.value

    async def get_preference_with_confidence(
        self,
        category: str,
        key: str,
    ) -> tuple[Any, float] | None:
        """
        Get preference value with its confidence score.

        Args:
            category: Category name
            key: Preference key

        Returns:
            Tuple of (value, confidence) or None if not found
        """
        prefs = await self.load()

        if category not in prefs.categories:
            return None

        cat = prefs.categories[category]
        if key not in cat.preferences:
            return None

        pref = cat.preferences[key]
        pref.access_count += 1
        return (pref.value, pref.confidence)

    async def learn_from_clarification(
        self,
        question_id: str,
        response: Any,
        context: str | None = None,
    ) -> None:
        """
        Learn a preference from a clarification response.

        Args:
            question_id: The clarification question ID
            response: User's response
            context: Optional context about the preference
        """
        # Use clarifications as the category
        category = "clarifications"
        source = f"clarification:{context}" if context else "clarification"

        await self.set_preference(
            category=category,
            key=question_id,
            value=response,
            source=source,
            confidence=0.8,  # Start with moderate confidence
        )

    async def suggest_default(
        self,
        category: str,
        key: str,
        min_confidence: float = 0.5,
    ) -> Any | None:
        """
        Suggest a default value based on learned preferences.

        Args:
            category: Category name
            key: Preference key
            min_confidence: Minimum confidence to return a suggestion

        Returns:
            Suggested value or None if confidence too low
        """
        result = await self.get_preference_with_confidence(category, key)
        if result is None:
            return None

        value, confidence = result
        if confidence >= min_confidence:
            return value
        return None

    async def get_category(
        self,
        category: str,
    ) -> dict[str, Any]:
        """
        Get all preferences in a category.

        Args:
            category: Category name

        Returns:
            Dictionary of key -> value
        """
        prefs = await self.load()

        if category not in prefs.categories:
            return {}

        cat = prefs.categories[category]
        return {k: p.value for k, p in cat.preferences.items()}

    async def clear_category(self, category: str) -> None:
        """Clear all preferences in a category."""
        prefs = await self.load()

        if category in prefs.categories:
            del prefs.categories[category]
            await self.save()

    async def clear_all(self) -> None:
        """Clear all preferences."""
        self._preferences = UserPreferences()
        await self.save()

    async def export_preferences(self) -> dict[str, Any]:
        """Export all preferences as a dictionary."""
        prefs = await self.load()
        return prefs.model_dump(mode="json")

    async def import_preferences(self, data: dict[str, Any]) -> None:
        """Import preferences from a dictionary."""
        self._preferences = UserPreferences.model_validate(data)
        await self.save()


# Global preference manager instance
_preference_manager: PreferenceManager | None = None


def get_preference_manager() -> PreferenceManager:
    """Get the global preference manager instance."""
    global _preference_manager
    if _preference_manager is None:
        _preference_manager = PreferenceManager()
    return _preference_manager
