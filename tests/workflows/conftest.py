"""
CP-07: Shared Test Fixtures — Workflow Tests (WF-01 to WF-09)
Firestore isolation: writes go to ci_test_* collections, never production.
Auto-cleanup: deletes ci_test_* docs after each test.
Run: API_GATEWAY_URL=http://localhost:8000 pytest tests/workflows/ -v
"""
import os
import pytest
import logging
import json
from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
test_logger = logging.getLogger("workflow_tests")


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """API Gateway URL. CI: release Docker stack. Local: localhost:8000."""
    return os.getenv("API_GATEWAY_URL", "http://localhost:8000")

@pytest.fixture(scope="session")
def integration_service_url() -> str:
    return os.getenv("INTEGRATION_SERVICE_URL", "http://localhost:8002")

@pytest.fixture(scope="session")
def agent_service_url() -> str:
    return os.getenv("AGENT_SERVICE_URL", "http://localhost:8006")

@pytest.fixture(scope="session")
def test_collection_prefix() -> str:
    """All test writes go to ci_test_* collections — NEVER production."""
    return os.getenv("TEST_COLLECTION_PREFIX", "ci_test_")

@pytest.fixture(scope="session")
def ci_test_user_id() -> str:
    return os.getenv("FIREBASE_CI_TEST_USER_ID", "ci-test-user-00000000")

@pytest.fixture(scope="session")
def ci_test_user_token() -> str:
    token = os.getenv("FIREBASE_CI_TEST_TOKEN", "")
    if not token:
        test_logger.warning("FIREBASE_CI_TEST_TOKEN not set — auth tests use mock tokens")
    return token

@pytest.fixture(scope="session")
def auth_headers(ci_test_user_token: str, ci_test_user_id: str) -> dict:
    return {
        "Authorization": f"Bearer {ci_test_user_token}",
        "X-User-ID": ci_test_user_id,
        "Content-Type": "application/json"
    }

@pytest.fixture
def mock_linkedin_auth_response() -> dict:
    return {"auth_url": "https://www.linkedin.com/oauth/v2/authorization?client_id=test&state=test-123", "state": "test-state-123"}

@pytest.fixture
def mock_linkedin_tokens() -> dict:
    return {"access_token": "AQXtest_token", "refresh_token": "AQXtest_refresh", "expires_in": 5183944}

@pytest.fixture
def mock_twitter_auth_response() -> dict:
    return {"success": True, "auth_url": "https://x.com/i/oauth2/authorize?client_id=test&state=456", "state": "test-state-456", "code_verifier": "test-verifier"}

@pytest.fixture
def mock_openai_content() -> dict:
    return {"refined_content": "AI-refined test content for CI validation.", "platforms": ["linkedin", "twitter"], "success": True}

@pytest.fixture
def mock_mcp_post_success() -> dict:
    return {"success": True, "post_id": "test-post-12345", "platform": "linkedin"}

@pytest.fixture
def mock_razorpay_order() -> dict:
    return {"id": "order_test123456", "amount": 99900, "currency": "INR", "status": "created"}

@pytest.fixture
def mock_firestore_db():
    """Mocked Firestore for unit-level tests that don't need real Firebase."""
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"connected": True, "access_token": "mock-token"}
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    mock_db.collection.return_value.add.return_value = (None, MagicMock(id="new-doc"))
    return mock_db


class WorkflowTestMonitor:
    """Track events, API calls, errors during test execution."""
    def __init__(self):
        self.events = []; self.api_calls = []; self.errors = []

    def log_event(self, event_type: str, details: dict):
        self.events.append({"ts": datetime.utcnow().isoformat(), "type": event_type})
        test_logger.info(f"[{event_type}] {json.dumps(details)}")

    def log_api_call(self, method: str, url: str, status: Optional[int] = None):
        self.api_calls.append({"method": method, "url": url, "status": status})

    def log_error(self, error_type: str, details: dict):
        self.errors.append({"type": error_type, "details": details})
        test_logger.error(f"ERROR [{error_type}]: {json.dumps(details)}")


@pytest.fixture
def test_monitor():
    return WorkflowTestMonitor()


@pytest.fixture(autouse=True)
def cleanup_test_data(test_collection_prefix, ci_test_user_id):
    """
    Runs AFTER every test. Deletes ci_test_* Firestore docs for CI test user.
    Only touches ci_test_* collections — never production data.
    """
    yield  # Test runs here

    try:
        proj = os.getenv("FIREBASE_PROJECT_ID")
        key = os.getenv("FIREBASE_PRIVATE_KEY", "")
        email = os.getenv("FIREBASE_CLIENT_EMAIL")
        if not all([proj, key, email]):
            return  # Unit-test mode — no real Firebase

        import firebase_admin
        from firebase_admin import credentials, firestore

        app_name = "ci-cleanup"
        try:
            app = firebase_admin.get_app(app_name)
        except ValueError:
            cred = credentials.Certificate({
                "type": "service_account", "project_id": proj,
                "private_key": key.replace("\\n", "\n"), "client_email": email,
                "token_uri": "https://oauth2.googleapis.com/token",
            })
            app = firebase_admin.initialize_app(cred, name=app_name)

        db = firestore.client(app=app)
        for coll in [f"{test_collection_prefix}users",
                     f"{test_collection_prefix}oauth_states",
                     f"{test_collection_prefix}scheduled_posts"]:
            try:
                for doc in db.collection(coll).where("test_run_id", "==", ci_test_user_id).limit(50).get():
                    doc.reference.delete()
            except Exception:
                pass
    except Exception as e:
        test_logger.debug(f"Cleanup skipped: {e}")
