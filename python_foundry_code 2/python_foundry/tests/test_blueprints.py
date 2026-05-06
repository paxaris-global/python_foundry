from app.services.intelligence.blueprint_registry import BlueprintRegistry


def test_blueprint_registry_loads() -> None:
    registry = BlueprintRegistry()
    names = registry.all_blueprints()

    assert "crm" in names
    crm = registry.get_blueprint("crm")
    assert crm["domain"] == "crm"
    assert "default_features" in crm
