
import pytest

from app.services.fuzzy_engine import (
    calculate_risk,
    classify_risk
)


def test_risk_is_between_zero_and_hundred():
    result = calculate_risk(30, 20, 25)

    assert 0 <= result <= 100


def test_high_risk_inputs():
    result = calculate_risk(95, 95, 95)

    assert result >= 65


def test_low_risk_inputs():
    result = calculate_risk(5, 5, 5)

    assert result <= 40


def test_invalid_negative_input():
    with pytest.raises(ValueError):
        calculate_risk(-1, 20, 30)


def test_invalid_input_above_hundred():
    with pytest.raises(ValueError):
        calculate_risk(20, 101, 30)


def test_classification():
    assert classify_risk(20) == "baixo"
    assert classify_risk(50) == "moderado"
    assert classify_risk(85) == "critico"
