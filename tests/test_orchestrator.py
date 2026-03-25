from app.services.generation.orchestrator import GenerationOrchestrator


class _FakeQuery:
    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return None


class _FakeDB:
    def query(self, *_args, **_kwargs):
        return _FakeQuery()

    def add(self, *_args, **_kwargs):
        return None

    def commit(self):
        return None

    def refresh(self, *_args, **_kwargs):
        return None


def test_orchestrator_parsing_and_domain() -> None:
    orchestrator = GenerationOrchestrator(db=_FakeDB())
    parsed = orchestrator.parse_prompt("Build a hotel management app with booking and billing")
    domain = orchestrator.classify_domain(parsed)
    blueprint = orchestrator.select_blueprint(domain, parsed)

    assert parsed["summary"]
    assert domain == "hotel_management"
    assert blueprint["domain"] == "hotel_management"
