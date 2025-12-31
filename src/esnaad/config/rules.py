"""Rules loader for ESNAAD.md project rules."""

from pathlib import Path

import aiofiles
import structlog

from esnaad.config.constants import RULES_FILE_NAME

logger = structlog.get_logger(__name__)

# Path to the rules folder (relative to this file's package)
RULES_FOLDER = Path(__file__).parent.parent / "rules"


class RulesLoader:
    """
    Loader for project-specific rules from ESNAAD.md.

    Rules are loaded once from the project root and cached.
    Missing files are handled gracefully (no error, just no rules).
    """

    # Class-level cache: working_directory -> rules content
    _cache: dict[str, str | None] = {}

    @classmethod
    def get_rules_path(cls, working_directory: Path) -> Path:
        """Get the path to the rules file."""
        return working_directory / RULES_FILE_NAME

    @classmethod
    async def load_rules(
        cls,
        working_directory: Path,
        force_reload: bool = False,
    ) -> str | None:
        """
        Load rules from ESNAAD.md in the working directory.

        Args:
            working_directory: Project root directory
            force_reload: If True, bypass cache and reload

        Returns:
            Rules content as string, or None if file doesn't exist
        """
        cache_key = str(working_directory.resolve())

        # Check cache first
        if not force_reload and cache_key in cls._cache:
            logger.debug("Rules loaded from cache", working_directory=cache_key)
            return cls._cache[cache_key]

        rules_path = cls.get_rules_path(working_directory)

        if not rules_path.exists():
            logger.debug(
                "No rules file found",
                path=str(rules_path),
            )
            cls._cache[cache_key] = None
            return None

        try:
            async with aiofiles.open(rules_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Strip and validate
            content = content.strip()
            if not content:
                logger.debug("Rules file is empty", path=str(rules_path))
                cls._cache[cache_key] = None
                return None

            logger.info(
                "Rules loaded",
                path=str(rules_path),
                size=len(content),
            )
            cls._cache[cache_key] = content
            return content

        except Exception as e:
            logger.warning(
                "Failed to load rules file",
                path=str(rules_path),
                error=str(e),
            )
            cls._cache[cache_key] = None
            return None

    @classmethod
    def load_rules_sync(
        cls,
        working_directory: Path,
        force_reload: bool = False,
    ) -> str | None:
        """
        Synchronous version of load_rules for contexts where async isn't available.

        Args:
            working_directory: Project root directory
            force_reload: If True, bypass cache and reload

        Returns:
            Rules content as string, or None if file doesn't exist
        """
        cache_key = str(working_directory.resolve())

        # Check cache first
        if not force_reload and cache_key in cls._cache:
            return cls._cache[cache_key]

        rules_path = cls.get_rules_path(working_directory)

        if not rules_path.exists():
            cls._cache[cache_key] = None
            return None

        try:
            content = rules_path.read_text(encoding="utf-8").strip()
            if not content:
                cls._cache[cache_key] = None
                return None

            cls._cache[cache_key] = content
            return content

        except Exception:
            cls._cache[cache_key] = None
            return None

    @classmethod
    def clear_cache(cls, working_directory: Path | None = None) -> None:
        """
        Clear the rules cache.

        Args:
            working_directory: Clear cache for specific directory, or all if None
        """
        if working_directory is None:
            cls._cache.clear()
            logger.debug("Rules cache cleared entirely")
        else:
            cache_key = str(working_directory.resolve())
            cls._cache.pop(cache_key, None)
            logger.debug("Rules cache cleared", working_directory=cache_key)

    @classmethod
    def is_cached(cls, working_directory: Path) -> bool:
        """Check if rules are cached for a directory."""
        cache_key = str(working_directory.resolve())
        return cache_key in cls._cache

    @classmethod
    async def load_rules_from_file(cls, rules_file: Path) -> str | None:
        """
        Load rules from a specific file path.

        Args:
            rules_file: Path to the rules file

        Returns:
            Rules content as string, or None if file doesn't exist
        """
        if not rules_file.exists():
            logger.warning(
                "Rules file not found",
                path=str(rules_file),
            )
            return None

        try:
            async with aiofiles.open(rules_file, "r", encoding="utf-8") as f:
                content = await f.read()

            content = content.strip()
            if not content:
                logger.debug("Rules file is empty", path=str(rules_file))
                return None

            logger.info(
                "Rules loaded from file",
                path=str(rules_file),
                size=len(content),
            )
            return content

        except Exception as e:
            logger.warning(
                "Failed to load rules file",
                path=str(rules_file),
                error=str(e),
            )
            return None

    @classmethod
    def get_preset_rules_path(cls, preset: str) -> Path:
        """
        Get the path to a preset rules file.

        Args:
            preset: Preset name (e.g., "CORE", "UI")

        Returns:
            Path to the rules file in the rules folder
        """
        return RULES_FOLDER / f"ESNAAD.{preset.upper()}.md"
