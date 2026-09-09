import os
import csv
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routes.advisory import (
    load_pesticides_dataset,
    load_regional_restrictions,
    check_regional_status,
    PESTICIDES_CSV,
    RESTRICTIONS_YAML
)

client = TestClient(app)


def test_pesticides_dataset_structure_and_fields():
    assert os.path.exists(PESTICIDES_CSV)
    with open(PESTICIDES_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        # Check required fields
        for expected in ["name", "active_ingredient", "crop_applicable", "dosage_ml_per_liter", "pre_harvest_interval_days", "eco_friendly_flag", "notes"]:
            assert expected in fieldnames

    dataset = load_pesticides_dataset()
    assert len(dataset) >= 10
    eco_items = [p for p in dataset if p["eco_friendly_flag"] is True]
    chem_items = [p for p in dataset if p["eco_friendly_flag"] is False]
    assert len(eco_items) >= 4
    assert len(chem_items) >= 4


def test_advisory_recommend_endpoint_basic():
    res = client.get("/advisory/recommend?disease=Early%20Blight&crop=Tomato")
    assert res.status_code == 200
    data = res.json()["data"]

    assert "cultural_practices" in data
    assert len(data["cultural_practices"]) >= 2

    assert "biological_controls" in data
    assert len(data["biological_controls"]) >= 1
    assert all(b["eco_friendly"] is True for b in data["biological_controls"])

    assert "chemical_options" in data
    assert len(data["chemical_options"]) >= 1

    # Check dosage and safety notes are included
    chem = data["chemical_options"][0]
    assert "dosage" in chem
    assert "pre_harvest_interval_days" in chem
    assert "safety_notes" in chem


def test_rule_engine_prefers_eco_friendly():
    res = client.get("/advisory/recommend?disease=Early%20Blight&crop=Tomato")
    assert res.status_code == 200
    data = res.json()["data"]
    ranked = data["all_ranked_recommendations"]
    assert len(ranked) >= 2

    # The top ranked recommendations should be Biological / Eco-Friendly Control
    first_item = ranked[0]
    assert first_item["category"] == "Biological / Eco-Friendly Control"
    assert first_item["eco_friendly"] is True
    assert first_item["rank_score"] >= 95.0


def test_regional_chemical_bans_kerala():
    # In Kerala, carbendazim, monocrotophos, paraquat, chlorpyrifos are strictly banned
    res = client.get("/advisory/recommend?disease=Blast&crop=Rice&region=Kerala")
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["regional_compliance"] is not None
    assert "Kerala" in data["regional_compliance"]["region"]
    banned_list = data["regional_compliance"]["banned_substances"]
    assert "carbendazim" in banned_list

    # Check that any chemical containing carbendazim has status banned and warning attached
    for chem in data["chemical_options"]:
        if "carbendazim" in chem["active_ingredient"].lower():
            assert chem["regional_status"] == "banned"
            assert "BANNED in Kerala" in chem["warning"]


def test_regional_chemical_bans_punjab_and_eu():
    # Punjab check
    res_punjab = client.get("/advisory/recommend?disease=Rust&crop=Wheat&region=Punjab")
    assert res_punjab.status_code == 200
    data_punjab = res_punjab.json()["data"]
    assert data_punjab["regional_compliance"] is not None

    # European Union check
    res_eu = client.get("/advisory/recommend?disease=Early%20Blight&crop=Potato&region=European%20Union")
    assert res_eu.status_code == 200
    data_eu = res_eu.json()["data"]
    for chem in data_eu["chemical_options"]:
        if "mancozeb" in chem["active_ingredient"].lower():
            assert chem["regional_status"] == "banned"
            assert "EU BANNED" in chem["warning"]


def test_advisory_missing_params_validation():
    # Missing crop
    res1 = client.get("/advisory/recommend?disease=Early%20Blight")
    assert res1.status_code == 422

    # Missing disease
    res2 = client.get("/advisory/recommend?crop=Tomato")
    assert res2.status_code == 422
