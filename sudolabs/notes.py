"""Smart note-taking system for SudoLabs.

Provides AI-enhanced note formatting, per-target markdown files,
a global pentest playbook, and automatic event-driven notes.
"""

from datetime import datetime
from pathlib import Path

from rich.panel import Panel
from rich.prompt import Prompt

from sudolabs.config import PROJECT_ROOT, get_auto_notes
from sudolabs.db import queries
from sudolabs.ui.theme import console


# ---------------------------------------------------------------------------
# Notes directory — auto-created in the project root, no prompts
# ---------------------------------------------------------------------------

NOTES_DIR = PROJECT_ROOT / "notes"


def _ensure_notes_dir():
    """Create PROJECT_ROOT/notes/ if it doesn't exist. No prompts."""
    try:
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Auto-note templates (no API calls — instant, free)
# ---------------------------------------------------------------------------

AUTO_NOTE_TEMPLATES = {
    "flag_captured": (
        "## [auto] Flag Captured: {stage_name}\n"
        "- Points: {points} | Time: {elapsed} | Hints: {hints}\n"
    ),
    "stage_advanced": (
        "## [auto] Stage Advanced: {stage_name}\n"
        "- Stage {stage_num}/{total_stages} | Elapsed: {elapsed}\n"
    ),
    "nmap_services": (
        "## [auto] Nmap Scan Results\n"
        "- Scan: {scan_type} | Ports: {port_list}\n"
    ),
    "hint_used": (
        "## [auto] Hint Used (Level {level})\n"
        "- Phase: {phase}\n"
    ),
    "milestone_reached": (
        "## [auto] Milestone: {milestone_name}\n"
        "- Time: {elapsed}\n"
    ),
    "session_started": (
        "# {target_name}\n"
        "> **Target:** {target_ip} | **Difficulty:** {difficulty}\n"
        "> **Session:** {session_id} | **Started:** {timestamp}\n"
        "\n---\n"
    ),
}

# ---------------------------------------------------------------------------
# AI prompt for note formatting
# ---------------------------------------------------------------------------

NOTE_FORMAT_PROMPT = """You are a cybersecurity note-taking assistant integrated into a penetration testing lab. The user has jotted down a quick observation during an active hacking session.

Your job:
1. ENHANCE the note with proper technical terminology and structure
2. PRESERVE the user's core observation — do not invent findings they did not mention
3. FORMAT as a concise markdown section with a ## heading and bullet points
4. If the note describes a REUSABLE technique (not specific to one target), extract a PLAYBOOK entry

TARGET CONTEXT:
- Target: {target_name}
- IP: {target_ip}
- Current Phase: {stage_name}
- Difficulty: {difficulty}
- Time Elapsed: {elapsed}

USER'S RAW NOTE: {raw_text}

Respond in EXACTLY this format:
---NOTE---
## <descriptive heading>
- <enhanced bullet points>
- <add relevant technical context>

> *Original: "{raw_text}"*
---PLAYBOOK---
## <technique category> - <technique name>
- **Technique:** <brief description>
- **When to use:** <applicable scenarios>
---END---

If no reusable technique applies, put NONE between the PLAYBOOK markers.
Keep the note under 8 lines and the playbook entry under 5 lines. Be concise."""


def get_auto_notes_enabled() -> bool:
    """Check if auto-notes are enabled."""
    return get_auto_notes()


# ---------------------------------------------------------------------------
# Interactive notebook menu
# ---------------------------------------------------------------------------

def notebook_menu(notes_mgr: "NoteManager", ai=None):
    """Interactive notebook menu called from the hunt loop.

    Displays a small Rich panel with [1] New Note / [2] View Notes.
    Uses Prompt.ask() which renders in the scroll area above the FixedBar.
    """
    from sudolabs.ui.panels import info_panel

    console.print(Panel(
        "  [bold bright_red][1][/bold bright_red] [dim]New Note[/dim]\n"
        "  [bold bright_red][2][/bold bright_red] [dim]View Notes[/dim]",
        title="[bold]NOTEBOOK[/bold]",
        border_style="bright_red",
        padding=(0, 2),
    ))

    choice = Prompt.ask("  [bold]Select[/bold]", choices=["1", "2"], default="1")

    if choice == "1":
        _new_note_flow(notes_mgr, ai)
    elif choice == "2":
        _view_notes_flow(notes_mgr, ai)


def _new_note_flow(notes_mgr: "NoteManager", ai=None):
    """Prompt for text, AI-enhance it, save as a new note."""
    from sudolabs.ui.panels import info_panel

    text = Prompt.ask("  [bold]Note[/bold]")
    if not text or not text.strip():
        console.print("  [dim]No note entered.[/dim]")
        return

    text = text.strip()
    stage_name = "Unknown"
    elapsed = "00:00:00"

    # Try to get stage/elapsed from the manager's context
    if hasattr(notes_mgr, "_stage_name"):
        stage_name = notes_mgr._stage_name
    if hasattr(notes_mgr, "_elapsed"):
        elapsed = notes_mgr._elapsed

    if ai and ai.is_available():
        with console.status("[bold green]Formatting note...[/bold green]"):
            formatted = notes_mgr.add_user_note(text, stage_name, elapsed)
        info_panel("Note Saved", formatted, border_style="green")
    else:
        notes_mgr.add_user_note(text, stage_name, elapsed)
        console.print("  [green]Note saved.[/green]")


def _view_notes_flow(notes_mgr: "NoteManager", ai=None):
    """List session notes, let user pick one to view, optionally append."""
    from sudolabs.ui.panels import info_panel

    notes = notes_mgr.get_session_notes()
    if not notes:
        console.print("  [dim]No notes yet. Use option [1] to create one.[/dim]")
        return

    # Display numbered list with timestamps and preview
    console.print("\n  [bold]Session Notes:[/bold]")
    for i, note in enumerate(notes, 1):
        tag = "[dim][auto][/dim] " if note["note_type"] == "auto" else ""
        preview = note["raw_text"][:80]
        if len(note["raw_text"]) > 80:
            preview += "..."
        console.print(f"  [bold bright_red][{i}][/bold bright_red] {tag}{preview}")

    console.print(f"  [bold bright_red][0][/bold bright_red] [dim]Back[/dim]")

    selection = Prompt.ask("  [bold]View note #[/bold]", default="0")

    if selection == "0":
        return

    try:
        idx = int(selection) - 1
        if idx < 0 or idx >= len(notes):
            console.print("  [red]Invalid selection.[/red]")
            return
    except ValueError:
        console.print("  [red]Invalid selection.[/red]")
        return

    selected = notes[idx]

    # Display the full note content
    display_text = selected["formatted_text"] or selected["raw_text"]
    timestamp = selected.get("created_at", "")
    console.print(Panel(
        display_text,
        title=f"[bold]Note #{idx + 1}[/bold] [dim]{timestamp}[/dim]",
        border_style="cyan",
        padding=(1, 2),
    ))

    # Offer to append more text
    append_text = Prompt.ask(
        "  [bold]Add to this note[/bold] [dim](Enter to skip)[/dim]",
        default="",
    )
    if append_text.strip():
        stage_name = "Unknown"
        elapsed = "00:00:00"
        if hasattr(notes_mgr, "_stage_name"):
            stage_name = notes_mgr._stage_name
        if hasattr(notes_mgr, "_elapsed"):
            elapsed = notes_mgr._elapsed

        notes_mgr.append_note(
            selected["id"], append_text.strip(), stage_name, elapsed
        )
        console.print("  [green]Note updated.[/green]")


# ---------------------------------------------------------------------------
# NoteManager
# ---------------------------------------------------------------------------

class NoteManager:
    """Manages per-target notes and the global pentest playbook.

    Instantiate once per hunt loop.  Handles:
    - AI-enhanced user notes
    - Template-based auto-notes (no API calls)
    - Persisting notes to DB and .md files
    - Global playbook extraction
    """

    def __init__(
        self,
        session_id: str,
        target_slug: str,
        target_name: str,
        target_ip: str,
        difficulty: str,
        ai=None,
    ):
        self.session_id = session_id
        self.target_slug = target_slug
        self.target_name = target_name
        self.target_ip = target_ip
        self.difficulty = difficulty
        self.ai = ai  # AIHelper instance (can be None)
        self._files_ok = False  # Track whether .md file I/O works

        # Mutable context — updated by the hunt loop before notebook_menu
        self._stage_name = "Unknown"
        self._elapsed = "00:00:00"

        # Set up file paths using the fixed NOTES_DIR
        self.notes_dir = NOTES_DIR
        safe_slug = target_slug.replace(":", "-").replace(" ", "-")
        self.target_file = self.notes_dir / f"{safe_slug}.md"
        self.playbook_file = self.notes_dir / "playbook.md"

        try:
            self._ensure_files()
        except Exception:
            # Notes directory is unusable — still save to DB, skip .md files
            pass

    # ── File initialization ────────────────────────────────

    def _ensure_files(self):
        """Create the notes directory and initialize files if needed."""
        _ensure_notes_dir()
        self.notes_dir.mkdir(parents=True, exist_ok=True)

        # Initialize target notes file with header
        if not self.target_file.exists():
            header = AUTO_NOTE_TEMPLATES["session_started"].format(
                target_name=self.target_name,
                target_ip=self.target_ip,
                difficulty=self.difficulty,
                session_id=self.session_id[:8],
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            )
            self.target_file.write_text(header, encoding="utf-8")

        # Initialize playbook if it doesn't exist
        if not self.playbook_file.exists():
            self.playbook_file.write_text(
                "# SudoLabs Pentest Playbook\n"
                "*Reusable techniques extracted from your hunts.*\n\n---\n\n",
                encoding="utf-8",
            )

        self._files_ok = True

    # ── User notes (AI-enhanced) ───────────────────────────

    def add_user_note(self, raw_text: str, stage_name: str, elapsed: str) -> str:
        """Add a user note, optionally AI-enhanced.

        Returns the formatted note text for display.
        """
        formatted = raw_text
        playbook_entry = None

        # Try AI formatting if available
        if self.ai and self.ai.is_available():
            try:
                formatted, playbook_entry = self._ai_format_note(
                    raw_text, stage_name, elapsed
                )
            except Exception:
                formatted = f"## Note\n- {raw_text}\n"

        else:
            formatted = f"## Note\n- {raw_text}\n"

        # Save to .md file
        self._append_to_target_file(formatted)

        # Save playbook entry if extracted
        if playbook_entry:
            self._append_to_playbook(playbook_entry)

        # Save to DB
        self._save_to_db(raw_text, formatted, "user", stage_name)

        return formatted

    # ── Append to existing note ─────────────────────────────

    def append_note(
        self, note_id: int, additional_text: str, stage_name: str, elapsed: str
    ):
        """Append text to an existing note (DB + .md file)."""
        formatted = additional_text

        # AI-enhance the appended text if available
        if self.ai and self.ai.is_available():
            try:
                formatted, playbook_entry = self._ai_format_note(
                    additional_text, stage_name, elapsed
                )
                if playbook_entry:
                    self._append_to_playbook(playbook_entry)
            except Exception:
                formatted = f"- {additional_text}\n"
        else:
            formatted = f"- {additional_text}\n"

        # Update DB
        try:
            queries.append_to_note(note_id, additional_text, formatted)
        except Exception:
            pass

        # Also append to the .md file
        self._append_to_target_file(formatted)

    # ── Auto-notes (template-based, no API) ────────────────

    def add_auto_note(self, template_key: str, **kwargs):
        """Add a template-based auto-note (no API call)."""
        if not get_auto_notes():
            return

        template = AUTO_NOTE_TEMPLATES.get(template_key)
        if not template:
            return

        try:
            text = template.format(**kwargs)
        except KeyError:
            return

        self._append_to_target_file(text)

        stage_name = kwargs.get("stage_name", kwargs.get("phase", ""))
        self._save_to_db(text.strip(), text.strip(), "auto", stage_name)

    # ── Read notes ─────────────────────────────────────────

    def get_session_notes(self) -> list[dict]:
        """Get all notes for the current session from the DB."""
        return queries.get_session_notes(self.session_id)

    # ── AI formatting ──────────────────────────────────────

    def _ai_format_note(
        self, raw_text: str, stage_name: str, elapsed: str
    ) -> tuple[str, str | None]:
        """Use Claude to enhance a note and optionally extract a playbook entry.

        This is a SEPARATE API call that does NOT pollute the
        hint/ask conversation history.

        Returns (formatted_note, playbook_entry_or_none).
        """
        client = self.ai._get_client()
        if not client:
            return f"## Note\n- {raw_text}\n", None

        prompt = NOTE_FORMAT_PROMPT.format(
            target_name=self.target_name,
            target_ip=self.target_ip,
            stage_name=stage_name,
            difficulty=self.difficulty,
            elapsed=elapsed,
            raw_text=raw_text,
        )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system="You are a concise cybersecurity note-taking assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        reply = response.content[0].text

        # Parse the structured response
        formatted = raw_text
        playbook = None

        if "---NOTE---" in reply and "---END---" in reply:
            parts = reply.split("---NOTE---")
            if len(parts) > 1:
                rest = parts[1]
                if "---PLAYBOOK---" in rest:
                    note_part, pb_part = rest.split("---PLAYBOOK---", 1)
                    formatted = note_part.strip()

                    pb_text = pb_part.replace("---END---", "").strip()
                    if pb_text and pb_text.upper() != "NONE":
                        playbook = pb_text
                else:
                    formatted = rest.replace("---END---", "").strip()
        else:
            # Fallback: use the entire reply as the note
            formatted = reply.strip()

        return formatted, playbook

    # ── File I/O ───────────────────────────────────────────

    def _append_to_target_file(self, markdown_block: str):
        """Append a markdown block to the target notes file."""
        if not self._files_ok:
            return
        try:
            with open(self.target_file, "a", encoding="utf-8") as f:
                f.write(f"\n{markdown_block}\n\n---\n")
        except OSError:
            pass  # Silently fail on file write errors

    def _append_to_playbook(self, entry: str):
        """Append a technique entry to the global playbook."""
        if not self._files_ok:
            return
        try:
            source_line = (
                f"- *Source: {self.target_slug} "
                f"({datetime.now().strftime('%Y-%m-%d')})*"
            )
            with open(self.playbook_file, "a", encoding="utf-8") as f:
                f.write(f"\n{entry}\n{source_line}\n\n---\n")
        except OSError:
            pass

    def _save_to_db(
        self,
        raw_text: str,
        formatted_text: str,
        note_type: str,
        stage_name: str = "",
    ):
        """Persist a note to the database."""
        try:
            queries.save_note(
                session_id=self.session_id,
                target_slug=self.target_slug,
                raw_text=raw_text,
                formatted_text=formatted_text,
                note_type=note_type,
                stage_name=stage_name,
            )
        except Exception:
            pass  # Don't crash the hunt on DB errors
