from core.schemas import Hypothesis
import pytest

def test_confidence_bounds():
    with pytest.raises(Exception): Hypothesis(hypothesis="x",confidence=1.5,reasoning="r")
