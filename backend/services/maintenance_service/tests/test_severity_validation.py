from datetime import date

import pytest
from pydantic import ValidationError

from services.maintenance_service.app.schemas import FailureCreate


def test_severity_accepted():
    f = FailureCreate(
        notification_date=date(2026, 4, 26), block="Y",
        failure_type="ESP_motor", severity="high",
    )
    assert f.severity == "high"


def test_severity_rejected():
    with pytest.raises(ValidationError):
        FailureCreate(
            notification_date=date(2026, 4, 26), block="Y",
            failure_type="ESP_motor", severity="catastrophic",
        )
