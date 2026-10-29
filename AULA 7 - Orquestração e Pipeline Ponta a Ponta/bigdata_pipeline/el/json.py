from .common import CaptureRun, capture_directory, run_single_capture


def capture(run: CaptureRun) -> dict[str, int]:
    source_dir = run.source / "json"
    if not source_dir.exists():
        source_dir = run.source / "files"
    return capture_directory(
        source_dir,
        run.landing / "json",
        run.state,
        "file_manifest",
        extensions={".json"},
    )


def main() -> None:
    run_single_capture("json", capture, "Captura incremental dos arquivos JSON.")


if __name__ == "__main__":
    main()