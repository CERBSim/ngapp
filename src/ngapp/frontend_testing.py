"""Utilities for frontent testing"""

import json
import os
from os import path

import pytest
from playwright.sync_api import Page
from pytest_check import check


class WebappLogin:
    """Login information for webapp tests"""

    request: pytest.FixtureRequest
    page: Page

    def __init__(self, request: pytest.FixtureRequest, page: Page):
        self.request = request
        self.page = page

    def create_model(self, model_id: str):
        """Create a model and wait until it is loaded"""
        page = self.page
        page.wait_for_selector(f'button[name="create_{model_id}"]')
        page.locator(f'button[name="create_{model_id}"]').click()
        page.locator("#q-loading").wait_for(state="attached")
        page.locator("#q-loading").wait_for(state="hidden")

    def compare_result(self, name: str, data: dict) -> None:
        """Compare data to reference data"""
        prefix = path.splitext(self.request.path)[0]
        node = self.request.node
        node_name = node.name.split("[")[0]
        suffix = f"{node_name}.{name}.json"
        result_dir = path.join(prefix, "results")
        os.makedirs(result_dir, exist_ok=True)

        with open(
            path.join(result_dir, suffix), "w", encoding="utf-8"
        ) as result_file:
            json.dump(data, result_file, indent=2, sort_keys=True)

        reference_path = path.join(prefix, "reference", suffix)
        have_reference_data = path.exists(reference_path)
        with check:
            assert have_reference_data
        if have_reference_data:
            with open(reference_path, encoding="utf-8") as reference_file:
                assert data == json.load(reference_file)

    def save_model(self, name: str = "") -> None:
        """Save the model and compare it to reference data"""
        with self.page.expect_request("**/model/*") as save_request:
            self.page.locator('button[name="saveModel"]').click()
        save_request = save_request.value
        assert save_request.failure is None
        data = save_request.post_data_json
        assert data is not None
        self.compare_result(name, data)


@pytest.fixture(name="login")
def login_fixture(page: Page, request: pytest.FixtureRequest) -> WebappLogin:
    """Login to the webapp and wait until the "Apps" page is loaded"""
    from webapp.auth import create_token

    token = create_token(
        sub="test", preferred_username="test", user_access={"test": 7}
    )
    page.goto(f"http://localhost:3000/apps#token={token}")
    page.wait_for_selector('button[name="create_DemoApp"]')
    return WebappLogin(request=request, page=page)


def example(login: WebappLogin) -> None:
    """Example function to use as starting point for new tests"""
    login.create_model("DemoApp")
    login.save_model("00_default")
    page = login.page
    page.pause()
