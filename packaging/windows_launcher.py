import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


APP_NAME = "LocalVoicePro"
DISPLAY_NAME = "Local Voice Pro"


def bundled_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def install_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(root) / APP_NAME


def desktop_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


def start_menu_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / DISPLAY_NAME
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / DISPLAY_NAME


def extract_payload(target: Path) -> None:
    payload = bundled_path("payload.zip")
    if not payload.exists():
        matches = sorted(bundled_path(".").glob("payload*.zip"))
        payload = matches[0] if matches else payload
    if not payload.exists():
        raise RuntimeError(f"payload.zip was not found beside the launcher: {payload}")

    marker = target / ".payload-version"
    target.mkdir(parents=True, exist_ok=True)
    payload_stamp = str(payload.stat().st_size)
    if marker.exists() and marker.read_text(encoding="utf-8").strip() == payload_stamp:
        return

    print(f"Installing files to {target} ...")
    with zipfile.ZipFile(payload, "r") as archive:
        archive.extractall(target)
    marker.write_text(payload_stamp, encoding="utf-8")


def extract_ffmpeg(target: Path) -> None:
    ffmpeg_exe = target / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
    ffprobe_exe = target / "tools" / "ffmpeg" / "bin" / "ffprobe.exe"
    if ffmpeg_exe.exists() and ffprobe_exe.exists():
        return

    ffmpeg_zip = target / "tools" / "ffmpeg.zip"
    if not ffmpeg_zip.exists():
        print("FFmpeg package was not bundled. The startup script will check global FFmpeg.")
        return

    print("Extracting bundled FFmpeg ...")
    extract_root = target / "tools" / "ffmpeg-extract"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ffmpeg_zip, "r") as archive:
        archive.extractall(extract_root)

    candidates = list(extract_root.rglob("ffmpeg.exe"))
    if not candidates:
        raise RuntimeError("Bundled FFmpeg archive did not contain ffmpeg.exe.")
    source_bin = candidates[0].parent
    dest_bin = target / "tools" / "ffmpeg" / "bin"
    dest_bin.mkdir(parents=True, exist_ok=True)
    for name in ("ffmpeg.exe", "ffprobe.exe"):
        src = source_bin / name
        if src.exists():
            shutil.copy2(src, dest_bin / name)


def write_command_files(target: Path) -> tuple[Path, Path]:
    start_cmd = target / "Start Local Voice Pro.cmd"
    stop_cmd = target / "Stop Local Voice Pro.cmd"
    start_script = target / "scripts" / "start-installed.ps1"
    stop_script = target / "scripts" / "stop-all.ps1"

    start_cmd.write_text(
        "\r\n".join(
            [
                "@echo off",
                f'cd /d "{target}"',
                f'powershell -NoProfile -ExecutionPolicy Bypass -File "{start_script}"',
                "pause",
                "",
            ]
        ),
        encoding="utf-8",
    )
    stop_cmd.write_text(
        "\r\n".join(
            [
                "@echo off",
                f'cd /d "{target}"',
                f'powershell -NoProfile -ExecutionPolicy Bypass -File "{stop_script}"',
                "pause",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return start_cmd, stop_cmd


def create_shortcut(shortcut_path: Path, target_path: Path, working_dir: Path, description: str) -> None:
    def ps_quote(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    shortcut_path.parent.mkdir(parents=True, exist_ok=True)
    script = (
        "$shell = New-Object -ComObject WScript.Shell; "
        f"$shortcut = $shell.CreateShortcut({ps_quote(str(shortcut_path))}); "
        f"$shortcut.TargetPath = {ps_quote(str(target_path))}; "
        f"$shortcut.WorkingDirectory = {ps_quote(str(working_dir))}; "
        f"$shortcut.Description = {ps_quote(description)}; "
        "$shortcut.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def create_shortcuts(target: Path) -> None:
    start_cmd, stop_cmd = write_command_files(target)
    menu = start_menu_dir()
    create_shortcut(menu / "Local Voice Pro.lnk", start_cmd, target, "Start Local Voice Pro")
    create_shortcut(menu / "Stop Local Voice Pro.lnk", stop_cmd, target, "Stop Local Voice Pro")
    try:
        create_shortcut(desktop_dir() / "Local Voice Pro.lnk", start_cmd, target, "Start Local Voice Pro")
    except Exception as exc:
        print(f"Desktop shortcut could not be created: {exc}")
    print(f"Start Menu shortcuts created: {menu}")


def run_start_script(target: Path) -> int:
    script = target / "scripts" / "start-installed.ps1"
    if not script.exists():
        raise RuntimeError(f"Startup script was not found: {script}")
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
    ]
    return subprocess.call(command, cwd=target)


def main() -> int:
    print("Local Voice Pro Windows setup")
    print("=============================")
    target = install_dir()
    try:
        extract_payload(target)
        extract_ffmpeg(target)
        create_shortcuts(target)
        return run_start_script(target)
    except Exception as exc:
        print("")
        print(f"Setup failed: {exc}")
        print("")
        try:
            input("Press Enter to exit...")
        except EOFError:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
