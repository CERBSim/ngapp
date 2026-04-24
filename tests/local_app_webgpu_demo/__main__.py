from ngapp.cli.serve_standalone import host_local_app

if __name__ == "__main__":
    host_local_app(
        "tests.local_app_webgpu_demo",
        start_browser=False,
        watch_code=False,
        dev_frontend=False,
    )