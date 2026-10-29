from .common import CaptureRun, capture_directory, run_single_capture


def capture(run: CaptureRun) -> dict[str, int]:
    source_dir = run.source / "csv"
    if not source_dir.exists():
        source_dir = run.source / "files"
    return capture_directory(
        source_dir,
        run.landing / "csv",
        run.state,
        "file_manifest",
        extensions={".csv"},
    )


def main() -> None:
    run_single_capture("csv", capture, "Captura incremental dos arquivos CSV.")


if __name__ == "__main__":
    main()