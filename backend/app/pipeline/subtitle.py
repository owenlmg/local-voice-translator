from dataclasses import dataclass
import re


@dataclass
class Cue:
    index: int
    start: float
    end: float
    text: str


SRT_TIME_RE = re.compile(
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d{3})"
)


def format_srt_time(seconds: float) -> str:
    seconds = max(0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds - hours * 3600) // 60)
    whole_seconds = int(seconds - hours * 3600 - minutes * 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"


def format_vtt_time(seconds: float) -> str:
    return format_srt_time(seconds).replace(",", ".")


def parse_srt_time(value: str) -> float:
    match = SRT_TIME_RE.search(value.strip())
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {value}")
    return (
        int(match.group("h")) * 3600
        + int(match.group("m")) * 60
        + int(match.group("s"))
        + int(match.group("ms")) / 1000
    )


def cues_from_segments(segments: list[dict]) -> list[Cue]:
    cues: list[Cue] = []
    for index, segment in enumerate(segments, start=1):
        cues.append(
            Cue(
                index=index,
                start=float(segment["start"]),
                end=float(segment["end"]),
                text=str(segment["text"]).strip(),
            )
        )
    return cues


def cues_to_srt(cues: list[Cue]) -> str:
    output: list[str] = []
    for index, cue in enumerate(cues, start=1):
        output.append(str(index))
        output.append(f"{format_srt_time(cue.start)} --> {format_srt_time(cue.end)}")
        output.append(cue.text.strip())
        output.append("")
    return "\n".join(output).strip() + "\n"


def cues_to_vtt(cues: list[Cue]) -> str:
    output = ["WEBVTT", ""]
    for index, cue in enumerate(cues, start=1):
        output.append(str(index))
        output.append(f"{format_vtt_time(cue.start)} --> {format_vtt_time(cue.end)}")
        output.append(cue.text.strip())
        output.append("")
    return "\n".join(output).strip() + "\n"


def cues_to_txt(cues: list[Cue]) -> str:
    return "\n".join(cue.text.strip() for cue in cues if cue.text.strip()) + "\n"


def parse_srt(content: str) -> list[Cue]:
    normalized = content.replace("\r\n", "\n").strip()
    if not normalized:
        return []
    cues: list[Cue] = []
    blocks = re.split(r"\n\s*\n", normalized)
    for fallback_index, block in enumerate(blocks, start=1):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 2:
            continue
        if "-->" in lines[0]:
            index = fallback_index
            timestamp = lines[0]
            text_lines = lines[1:]
        else:
            index = int(lines[0]) if lines[0].isdigit() else fallback_index
            timestamp = lines[1]
            text_lines = lines[2:]
        start_raw, end_raw = [item.strip() for item in timestamp.split("-->", 1)]
        cues.append(Cue(index=index, start=parse_srt_time(start_raw), end=parse_srt_time(end_raw), text="\n".join(text_lines)))
    return cues

