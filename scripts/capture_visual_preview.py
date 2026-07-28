#!/usr/bin/env python3
"""Rasterize a canonical SVG blueprint with a Chromium-compatible browser."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def build_browser_command(
    browser: Path, source_svg: Path, output_png: Path
) -> list[str]:
    return [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-color-profile=srgb",
        "--force-device-scale-factor=1",
        "--window-size=1440,900",
        f"--screenshot={output_png}",
        source_svg.resolve().as_uri(),
    ]


def capture(source_svg: Path, output_png: Path, browser: Path) -> None:
    if source_svg.suffix.lower() != ".svg":
        raise ValueError("input must use the .svg extension")
    if not source_svg.is_file():
        raise ValueError(f"SVG file does not exist: {source_svg}")
    if not browser.is_file():
        raise ValueError(f"browser executable does not exist: {browser}")
    if not os.access(browser, os.X_OK):
        raise ValueError(f"browser is not executable: {browser}")

    output_png.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{output_png.stem}-",
            suffix=".png",
            dir=output_png.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        result = subprocess.run(
            build_browser_command(browser, source_svg, temporary_path),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise RuntimeError(f"browser capture failed: {detail}")
        try:
            header = temporary_path.read_bytes()[:8]
        except OSError as exc:
            raise RuntimeError(f"browser did not create a readable PNG: {exc}") from exc
        if header != PNG_SIGNATURE:
            raise RuntimeError("browser output is not a PNG file")
        os.replace(temporary_path, output_png)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--browser", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        capture(args.svg, args.output, args.browser)
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Captured SVG blueprint to {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
