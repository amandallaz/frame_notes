import re
from dataclasses import dataclass, field
from pathlib import Path

from .models import frame_display

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMPORT_FRAMES = 45


@dataclass
class ImportResult:
    imported: int = 0
    skipped: list[str] = field(default_factory=list)
    leaders: list[str] = field(default_factory=list)


def _natural_sort_key(filename: str):
    """Sort 2 before 10 — labs often use numeric filenames."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", filename)
    ]


def _leader_frame_number(leader_index: int, leader_count: int) -> int:
    """Map leader file index to frame number: 00 (-1), 0 (0), then 1…"""
    return leader_index - leader_count + 1


def _save_frame_image(roll, frame_num: int, name: str, upload) -> None:
    from .models import FrameNote

    frame, _created = FrameNote.objects.get_or_create(
        roll=roll,
        frame_number=frame_num,
        defaults={"note": ""},
    )
    if frame.image.name:
        frame.image.delete(save=False)
    upload.seek(0)
    ext = Path(name).suffix.lower() or ".jpg"
    frame.scan_filename = name
    frame.image.save(f"frame_{frame_display(frame_num)}{ext}", upload, save=True)


def import_roll_folder(
    roll, uploaded_files, *, reverse=False, first_file_index=1
) -> ImportResult:
    """
    Map sorted filenames to film frame numbers.

    Files before first_file_index become leaders (00, 0, …) then 1, 2, 3…
    """
    result = ImportResult()
    if not uploaded_files:
        result.skipped.append("No files selected.")
        return result

    images = []
    for upload in uploaded_files:
        name = Path(upload.name).name
        if Path(name).suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        images.append((name, upload))

    if not images:
        result.skipped.append("No image files found (jpg, jpeg, png, webp).")
        return result

    images.sort(key=lambda item: _natural_sort_key(item[0]))
    if reverse:
        images.reverse()

    first_file_index = max(1, first_file_index)
    if first_file_index > len(images):
        result.skipped.append(
            f"File #{first_file_index} not found — only {len(images)} images."
        )
        return result

    leaders = images[: first_file_index - 1]
    main = images[first_file_index - 1 :]

    for i, (name, upload) in enumerate(leaders):
        frame_num = _leader_frame_number(i, len(leaders))
        _save_frame_image(roll, frame_num, name, upload)
        result.imported += 1
        result.leaders.append(frame_display(frame_num))

    needed_frames = len(main)
    if needed_frames > roll.max_frames:
        new_max = min(needed_frames, MAX_IMPORT_FRAMES)
        if needed_frames > MAX_IMPORT_FRAMES:
            result.skipped.append(
                f"Only importing first {MAX_IMPORT_FRAMES} main frames "
                f"({needed_frames} after frame 1)."
            )
            main = main[:MAX_IMPORT_FRAMES]
            needed_frames = MAX_IMPORT_FRAMES
        roll.max_frames = new_max
        roll.save(update_fields=["max_frames"])

    for index, (name, upload) in enumerate(main):
        frame_num = index + 1
        _save_frame_image(roll, frame_num, name, upload)
        result.imported += 1

    return result


def set_frame_one(roll, source_frame_number: int) -> int:
    """Shift every frame on the roll so source_frame_number becomes frame 1."""
    return reanchor_roll_frames(roll, source_frame_number, anchor_frame_number=1)


def reanchor_roll_frames(roll, source_frame_number: int, anchor_frame_number: int) -> int:
    """
    Shift every frame on the roll so source_frame_number becomes anchor_frame_number.
    Returns the delta applied, or 0 if unchanged.
    """
    from .models import FrameNote

    frames = list(FrameNote.objects.filter(roll=roll).order_by("frame_number"))
    if not frames:
        return 0
    if not any(f.frame_number == source_frame_number for f in frames):
        raise ValueError(f"No frame {source_frame_number} on this roll.")
    delta = anchor_frame_number - source_frame_number
    if delta == 0:
        return 0
    originals = {frame.pk: frame.frame_number for frame in frames}
    for i, frame in enumerate(frames):
        frame.frame_number = 10_000 + i
        frame.save(update_fields=["frame_number"])
    for frame in frames:
        frame.frame_number = originals[frame.pk] + delta
        frame.save(update_fields=["frame_number"])
    return delta


def clear_roll_images(roll) -> int:
    """Remove all scans on a roll. Keeps text notes; drops image-only frames."""
    removed = 0
    for frame in roll.frames.all():
        if not frame.image.name:
            continue
        frame.image.delete(save=False)
        frame.scan_filename = ""
        removed += 1
        if not frame.note.strip():
            frame.delete()
        else:
            frame.save(update_fields=["scan_filename"])
    return removed
