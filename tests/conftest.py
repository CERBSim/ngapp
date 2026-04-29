from pathlib import Path

import ngapp.e2e_webgpu as e2e_webgpu

pytest_plugins = ["ngapp.e2e_webgpu"]

TESTS_DIR = Path(__file__).parent

e2e_webgpu.configure(
    output_dir=TESTS_DIR / "output",
    baseline_dir=TESTS_DIR / "baselines",
)
