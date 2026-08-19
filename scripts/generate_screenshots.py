"""Render clean, high-resolution evidence screenshots from executed notebooks and demo outputs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = ROOT / "submission" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size: int = 15):
    # Try common monospace fonts on Windows/Linux
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/lucon.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_terminal_card(title: str, lines: list[str], output_path: Path, width: int = 1000):
    font = get_font(15)
    title_font = get_font(17)

    line_height = 22
    padding = 24
    header_height = 48
    height = header_height + padding * 2 + len(lines) * line_height

    img = Image.new("RGB", (width, height), color="#1e1e2e")
    draw = ImageDraw.Draw(img)

    # Window titlebar
    draw.rectangle([0, 0, width, header_height], fill="#181825")

    # Window buttons (red, yellow, green dots)
    draw.ellipse([16, 18, 28, 30], fill="#f38ba8")
    draw.ellipse([36, 18, 48, 30], fill="#f9e2af")
    draw.ellipse([56, 18, 68, 30], fill="#a6e3a1")

    # Title text
    draw.text((80, 14), title, fill="#cdd6f4", font=title_font)

    # Content
    y = header_height + padding
    for line in lines:
        if line.startswith("PASS") or "PASS" in line:
            fill_color = "#a6e3a1"  # green
        elif line.startswith("WARN") or "FAIL" in line or "Error" in line:
            fill_color = "#f38ba8"  # red
        elif line.startswith("==") or line.startswith("--"):
            fill_color = "#89b4fa"  # blue
        elif line.startswith("QUERY") or line.startswith("["):
            fill_color = "#fab387"  # orange
        elif line.startswith("  type") or line.startswith("  user_id") or line.startswith("  mode"):
            fill_color = "#f9e2af"  # yellow
        else:
            fill_color = "#cdd6f4"  # standard text

        draw.text((padding, y), line, fill=fill_color, font=font)
        y += line_height

    img.save(output_path, "PNG")
    print(f"Saved: {output_path.name}")


def extract_cell_outputs(nb_path: Path) -> list[str]:
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    all_lines = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            for out in cell.get("outputs", []):
                if "text" in out:
                    raw = "".join(out["text"])
                    all_lines.extend(raw.splitlines())
                elif "data" in out and "text/plain" in out["data"]:
                    raw = "".join(out["data"]["text/plain"])
                    all_lines.extend(raw.splitlines())
    return all_lines


def main():
    print("Generating screenshot evidence...")

    # NB1
    nb1_lines = extract_cell_outputs(ROOT / "notebooks" / "01_embeddings_index.ipynb")
    render_terminal_card(
        "NB1: 01_embeddings_index.ipynb (1000 Vectors Indexed + Top-5 Similarity Search)",
        nb1_lines,
        SCREENSHOTS_DIR / "01_nb1_embeddings_index.png",
    )

    # NB2
    nb2_lines = extract_cell_outputs(ROOT / "notebooks" / "02_hybrid_search_rrf.ipynb")
    render_terminal_card(
        "NB2: 02_hybrid_search_rrf.ipynb (Average Precision@10 & Query Type Slices)",
        nb2_lines,
        SCREENSHOTS_DIR / "02_nb2_hybrid_search_rrf.png",
    )

    # NB3
    nb3_lines = extract_cell_outputs(ROOT / "notebooks" / "03_search_api_benchmark.ipynb")
    render_terminal_card(
        "NB3: 03_search_api_benchmark.ipynb (FastAPI /search & P50/P95/P99 Latency Table)",
        nb3_lines,
        SCREENSHOTS_DIR / "03_nb3_search_api_benchmark.png",
    )

    # NB4
    nb4_lines = extract_cell_outputs(ROOT / "notebooks" / "04_feast_feature_store.ipynb")
    render_terminal_card(
        "NB4: 04_feast_feature_store.ipynb (Feast 3 Views, Materialize, P99 < 10ms & PIT Join)",
        nb4_lines,
        SCREENSHOTS_DIR / "04_nb4_feast_feature_store.png",
    )

    # NB5
    nb5_lines = extract_cell_outputs(ROOT / "notebooks" / "05_filtered_search.ipynb")
    render_terminal_card(
        "NB5: 05_filtered_search.ipynb (Selectivity Recall Table & Over-fetch Ladder)",
        nb5_lines,
        SCREENSHOTS_DIR / "05_nb5_filtered_search.png",
    )

    # NB6
    nb6_lines = extract_cell_outputs(ROOT / "notebooks" / "06_agent_retrieval.ipynb")
    render_terminal_card(
        "NB6: 06_agent_retrieval.ipynb (Agentic vs Single-Shot at Budget 16 + Build Context)",
        nb6_lines,
        SCREENSHOTS_DIR / "06_nb6_agent_retrieval.png",
    )

    # NB7
    nb7_lines = extract_cell_outputs(ROOT / "notebooks" / "07_semantic_cache.ipynb")
    render_terminal_card(
        "NB7: 07_semantic_cache.ipynb (Threshold Sweep 2 Columns + Tenant Isolation Demo)",
        nb7_lines,
        SCREENSHOTS_DIR / "07_nb7_semantic_cache.png",
    )

    # NB8
    nb8_lines = extract_cell_outputs(ROOT / "notebooks" / "08_feature_engineering.ipynb")
    render_terminal_card(
        "NB8: 08_feature_engineering.ipynb (Target Encoding Leakage Gap + PIT vs Latest + ODFV)",
        nb8_lines,
        SCREENSHOTS_DIR / "08_nb8_feature_engineering.png",
    )

    # Bonus Demo
    res = subprocess.run(
        [sys.executable, str(ROOT / "bonus" / "demo.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    demo_lines = res.stdout.splitlines()
    render_terminal_card(
        "Bonus: bonus/demo.py (Hybrid Memory 5-Query Demo Execution)",
        demo_lines,
        SCREENSHOTS_DIR / "09_bonus_demo.png",
    )

    print(f"\nSuccessfully generated {len(list(SCREENSHOTS_DIR.glob('*.png')))} evidence screenshots.")


if __name__ == "__main__":
    main()
