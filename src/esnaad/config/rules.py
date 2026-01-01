"""Rules loader for ESNAAD.md project rules."""

import re
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
    def _process_includes(
        cls,
        content: str,
        base_path: Path,
        seen: set[Path] | None = None,
    ) -> str:
        """
        Process include directives in rules content.

        Syntax: <!-- #include FILENAME.md -->

        Args:
            content: The content to process
            base_path: Directory for resolving relative includes
            seen: Set of already-included paths (circular reference prevention)

        Returns:
            Content with includes resolved
        """
        if seen is None:
            seen = set()

        pattern = r'<!--\s*#include\s+(.+?)\s*-->'

        def replace_include(match: re.Match) -> str:
            include_file = match.group(1).strip()
            include_path = (base_path / include_file).resolve()

            # Prevent circular includes
            if include_path in seen:
                logger.warning(
                    "Circular include detected",
                    file=include_file,
                    path=str(include_path),
                )
                return f"[Circular include: {include_file}]"

            if include_path.exists():
                seen.add(include_path)
                try:
                    included = include_path.read_text(encoding="utf-8")
                    logger.debug(
                        "Include resolved",
                        file=include_file,
                        size=len(included),
                    )
                    # Recursive processing for nested includes
                    return cls._process_includes(included, include_path.parent, seen)
                except Exception as e:
                    logger.warning(
                        "Failed to read include file",
                        file=include_file,
                        error=str(e),
                    )
                    return f"[Include error: {include_file}]"

            logger.warning(
                "Include file not found",
                file=include_file,
                path=str(include_path),
            )
            return f"[Include not found: {include_file}]"

        return re.sub(pattern, replace_include, content)

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

            # Process includes relative to the rules file's directory
            content = cls._process_includes(content, rules_path.parent)

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

            # Process includes relative to the rules file's directory
            content = cls._process_includes(content, rules_path.parent)

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
        Load rules from a specific file path with include processing.

        Args:
            rules_file: Path to the rules file

        Returns:
            Rules content as string with includes resolved, or None if file doesn't exist
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

            # Process includes relative to the rules file's directory
            content = cls._process_includes(content, rules_file.parent)

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
    def load_rules_from_file_sync(cls, rules_file: Path) -> str | None:
        """
        Synchronous version of load_rules_from_file with include processing.

        Args:
            rules_file: Path to the rules file

        Returns:
            Rules content as string with includes resolved, or None if file doesn't exist
        """
        if not rules_file.exists():
            logger.warning(
                "Rules file not found",
                path=str(rules_file),
            )
            return None

        try:
            content = rules_file.read_text(encoding="utf-8").strip()
            if not content:
                logger.debug("Rules file is empty", path=str(rules_file))
                return None

            # Process includes relative to the rules file's directory
            content = cls._process_includes(content, rules_file.parent)

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
        Get the path to a preset rules file in its subfolder.

        Args:
            preset: Preset name (e.g., "CORE", "UI")

        Returns:
            Path to the rules file in the preset's subfolder
        """
        preset_lower = preset.lower()
        return RULES_FOLDER / preset_lower / f"ESNAAD.{preset.upper()}.md"
