"""Deploy an app from GitHub Actions or GitLab CI, without a stored token.

    python -m ngapp.cli.deploy_ci <backend_url> <app_id> <app_module>.appconfig

The repository and branch must be registered as trusted publisher of the app (app admin
page, "Deploy from CI", which also shows the pipeline definition). The OIDC token of the
job is exchanged for a short-lived token that may only update this app.
GitHub: the job needs ``permissions: id-token: write``.
GitLab: the job needs ``id_tokens: NGAPP_ID_TOKEN: aud: <backend_url>``.
"""

import argparse
import os
from urllib.parse import quote

import certifi
import orjson
import urllib3

from .. import api
from ..utils import EnvironmentType, set_environment
from .deploy import load_config, upload_app


def id_token(audience: str) -> str:
    """OIDC token of the CI job for the audience"""
    if "ACTIONS_ID_TOKEN_REQUEST_URL" in os.environ:
        url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"] + "&audience=" + quote(audience, safe="")
        headers = {"Authorization": "bearer " + os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]}
        http = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())
        response = http.request("GET", url, headers=headers)
        if response.status >= 400:
            raise SystemExit(f"GitHub refused the id token: {response.data.decode()}")
        return orjson.loads(response.data)["value"]
    if os.environ.get("NGAPP_ID_TOKEN"):
        return os.environ["NGAPP_ID_TOKEN"]
    raise SystemExit(
        "No CI id token: GitHub jobs need 'permissions: id-token: write', GitLab jobs "
        f"'id_tokens: NGAPP_ID_TOKEN: aud: {audience}'"
    )


def main():
    parser = argparse.ArgumentParser(description="Deploy an app from a CI pipeline")
    parser.add_argument("backend_url")
    parser.add_argument("app_id", type=int)
    parser.add_argument("config_module", help="module with the AppConfig, e.g. myapp.appconfig")
    parser.add_argument(
        "--wheels",
        metavar="DIR",
        help="also upload the wheels in DIR (prebuilt compute dependencies)",
    )
    args = parser.parse_args()

    config = load_config(args.config_module)
    env = set_environment(EnvironmentType.LOCAL_APP)
    env.set_backend(args.backend_url, "")
    data = {"app_id": args.app_id, "id_token": id_token(args.backend_url)}
    env.set_backend(args.backend_url, api.post("/ci/token", data)["token"])
    upload_app(
        config,
        args.app_id,
        reload_dependencies=config.frontend_dependencies,
        wheels_dir=args.wheels,
    )
    print(f"Deployed '{config.name}' (id {args.app_id}) to {args.backend_url}")


if __name__ == "__main__":
    main()
