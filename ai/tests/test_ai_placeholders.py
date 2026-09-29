"""Tests for AI module placeholders."""
from ai.demand_forecasting import predict as demand_predict
from ai.stockout_prediction import predict as stockout_predict


def test_ai_placeholders():
    demand_res = demand_predict.placeholder()
    assert demand_res["status"] == "placeholder"

    stockout_res = stockout_predict.placeholder()
    assert stockout_res["status"] == "placeholder"
