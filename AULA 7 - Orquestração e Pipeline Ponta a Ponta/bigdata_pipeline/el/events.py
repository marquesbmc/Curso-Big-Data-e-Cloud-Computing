from .common import CaptureRun, capture_directory, run_single_capture


def capture(run: CaptureRun) -> dict[str, int]:
    return capture_directory(
        run.source / "events",
        run.landing / "events",
        run.state,
        "event_manifest",
    )


def main() -> None:
    run_single_capture("events", capture, "Captura incremental dos eventos JSON Lines.")


if __name__ == "__main__":
    main()