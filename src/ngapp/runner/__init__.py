"""Compute runner: pulls jobs from a webapp backend over HTTPS and runs them in sandboxes.

    pip install "ngapp[runner]"
    python -m ngapp.runner --host webapp.example.com --token ... --cpus 8 --memory 32GB
"""
