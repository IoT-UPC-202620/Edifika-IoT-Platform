import json, pathlib, pytest
from jsonschema import Draft202012Validator, FormatChecker
ROOT = pathlib.Path(__file__).resolve().parents[1] / "contracts"
SCHEMAS, EXAMPLES = ROOT / "schemas", ROOT / "examples"
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def validator(rel): return Draft202012Validator(load(SCHEMAS / rel), format_checker=FormatChecker())
PAIRS = [(e, e.relative_to(EXAMPLES).with_suffix(".schema.json"))
         for e in sorted(EXAMPLES.rglob("*.json")) if e.parent.name != "envelope"]

@pytest.mark.parametrize("example,schema", PAIRS, ids=lambda x: str(x))
def test_example_is_valid(example, schema):
    validator(schema).validate(load(example))

def test_every_schema_has_an_example():
    schemas = {p.relative_to(SCHEMAS) for p in SCHEMAS.rglob("*.schema.json")}
    assert schemas == {s for _, s in PAIRS}

def test_envelope_examples_match_envelope_and_payload():
    envelopes = sorted((EXAMPLES / "envelope").glob("*.json"))
    assert {e.stem for e in envelopes} == {p.stem.removesuffix(".schema") for p in (SCHEMAS / "payloads").glob("*.json")}
    for env in envelopes:
        body = load(env)
        validator("envelope.schema.json").validate(body)
        validator(f"payloads/{body['eventType']}.schema.json").validate(body["payload"])

def test_enum_typo_is_rejected():
    body = load(EXAMPLES / "payloads/AccessAttempt.json"); body["accessMode"] = "FREE_ACESS"
    assert list(validator("payloads/AccessAttempt.schema.json").iter_errors(body))

def test_extra_payload_field_is_accepted():
    body = load(EXAMPLES / "payloads/Reading.json"); body["newField"] = 1
    validator("payloads/Reading.schema.json").validate(body)

def test_occurred_at_without_zone_is_rejected():
    body = load(EXAMPLES / "envelope/AccessAttempt.json"); body["occurredAt"] = "2026-10-23T15:04:05"
    assert list(validator("envelope.schema.json").iter_errors(body))

def test_sync_reservation_requires_authorized_ids():
    body = load(EXAMPLES / "sync.json"); del body["reservations"][0]["authorizedResidentIds"]
    assert list(validator("sync.schema.json").iter_errors(body))
