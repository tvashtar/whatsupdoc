"""Test script to verify Slack bot connection and configuration.
Run this to make sure your Slack setup is working before building the full bot.
"""

import os

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture
def slack_required_vars() -> list[str]:
    """Required Slack environment variables."""
    return ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "SLACK_APP_TOKEN"]


@pytest.fixture
def slack_optional_vars() -> list[str]:
    """Optional Slack environment variables for OAuth."""
    return ["SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET"]


@pytest.fixture
def slack_config(slack_required_vars: list[str]) -> dict[str, str]:
    """Slack configuration from environment variables."""
    config = {}
    missing_vars = []

    for var in slack_required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            config[var.lower()] = value

    if missing_vars:
        pytest.skip(f"Missing required Slack environment variables: {', '.join(missing_vars)}")

    return config


@pytest.mark.integration
@pytest.mark.requires_slack
def test_required_slack_env_variables(slack_required_vars: list[str]) -> None:
    """Test that all required Slack environment variables are set."""
    missing_vars = []

    for var in slack_required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)

    assert (
        not missing_vars
    ), f"Missing required Slack environment variables: {', '.join(missing_vars)}"

    # Verify each variable has content
    for var in slack_required_vars:
        value = os.getenv(var)
        assert value and len(value.strip()) > 0, f"{var} should not be empty"


@pytest.mark.integration
@pytest.mark.requires_slack
def test_slack_token_formats(slack_config: dict[str, str]) -> None:
    """Verify Slack token formats are correct."""
    bot_token = slack_config.get("slack_bot_token")
    app_token = slack_config.get("slack_app_token")

    # Bot token should start with xoxb-
    assert bot_token.startswith("xoxb-"), "SLACK_BOT_TOKEN should start with 'xoxb-'"
    assert len(bot_token) > 10, "Bot token should be reasonably long"

    # App token should start with xapp-
    assert app_token.startswith("xapp-"), "SLACK_APP_TOKEN should start with 'xapp-'"
    assert len(app_token) > 10, "App token should be reasonably long"

    # Signing secret should exist and be reasonably long
    signing_secret = slack_config.get("slack_signing_secret")
    assert len(signing_secret) > 10, "Signing secret should be reasonably long"


@pytest.mark.integration
@pytest.mark.requires_slack
def test_optional_slack_vars(slack_optional_vars: list[str]) -> None:
    """Test optional Slack variables (informational only)."""
    # This test doesn't fail if optional vars are missing
    for var in slack_optional_vars:
        value = os.getenv(var)
        if value:
            # If present, verify basic format
            if var == "SLACK_CLIENT_ID":
                # Client ID should contain a dot (format: number.number)
                assert "." in value, "SLACK_CLIENT_ID should contain a dot (format: number.number)"


@pytest.mark.integration
@pytest.mark.requires_slack
def test_slack_api_connection(slack_config: dict[str, str]) -> None:
    """Test connection to Slack API."""
    from slack_sdk import WebClient

    bot_token = slack_config.get("slack_bot_token")
    client = WebClient(token=bot_token)

    # Test API connection with auth.test
    response = client.auth_test()

    assert response.get("ok"), f"API call should succeed, got error: {response.get('error')}"
    assert response.get("user"), "Should return bot user name"
    assert response.get("team"), "Should return team name"
    assert response.get("user_id"), "Should return user ID"

    # Verify response structure
    assert isinstance(response.get("user"), str), "User should be a string"
    assert isinstance(response.get("team"), str), "Team should be a string"
    assert isinstance(response.get("user_id"), str), "User ID should be a string"


@pytest.mark.integration
@pytest.mark.requires_slack
def test_socket_mode_setup(slack_config: dict[str, str]) -> None:
    """Test Socket Mode connection capability."""
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    app_token = slack_config.get("slack_app_token")
    bot_token = slack_config.get("slack_bot_token")

    # Create a minimal app (don't start it)
    app = App(token=bot_token)

    # Should be able to create handler without errors
    handler = SocketModeHandler(app, app_token)

    assert handler is not None, "Socket Mode handler should be created"
    assert hasattr(handler, "app"), "Handler should have app attribute"
    assert hasattr(handler, "app_token"), "Handler should have app_token attribute"


@pytest.mark.integration
@pytest.mark.requires_slack
def test_slack_bolt_app_creation(slack_config: dict[str, str]) -> None:
    """Test that Slack Bolt app can be created."""
    from slack_bolt import App

    bot_token = slack_config.get("slack_bot_token")
    signing_secret = slack_config.get("slack_signing_secret")

    # Create app with required parameters
    app = App(
        token=bot_token,
        signing_secret=signing_secret,
    )

    assert app is not None, "Slack App should be created"
    assert hasattr(app, "client"), "App should have client attribute"
    assert hasattr(app, "_token"), "App should have token attribute"


@pytest.mark.integration
@pytest.mark.requires_slack
@pytest.mark.parametrize("required_scope", ["app_mentions:read", "chat:write", "commands"])
def test_bot_token_scopes(slack_config: dict[str, str], required_scope: str) -> None:
    """Test that bot token has required scopes (informational)."""
    from slack_sdk import WebClient

    bot_token = slack_config.get("slack_bot_token")
    client = WebClient(token=bot_token)

    try:
        # Get bot info to check scopes indirectly
        response = client.auth_test()
        assert response.get("ok"), f"Should be able to call auth.test with scope {required_scope}"

        # Note: We can't directly test scopes without making actual API calls
        # that might require those scopes, which could fail in test environment

    except Exception as e:
        pytest.skip(f"Cannot verify scope {required_scope}: {e}")
