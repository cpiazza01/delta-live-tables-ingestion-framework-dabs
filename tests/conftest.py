import pytest
from lakeflow_ingestion_framework.cli import make_jinja_env
from tests.helpers import TEMPLATES_DIR


@pytest.fixture
def jinja_env():
    return make_jinja_env(TEMPLATES_DIR)
