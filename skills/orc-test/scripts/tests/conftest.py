"""`runner._ACTIVE` is module-level state (v23): no test inherits another's container."""

import pytest
from orc_test import runner


@pytest.fixture(autouse=True)
def no_container():
    runner.use(None)
    yield
    runner.use(None)
