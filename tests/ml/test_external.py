import json

from ml.validation.external import iter_json_array


def test_streams_elements_identically_to_json_load(tmp_path):
    records = [
        {"id": "mp-1", "formula": "Na{Cl}", "gap pbe": 5.0, "atoms": {"elements": ["Na", "Cl"], "coords": [[0, 0, 0]]}},
        {"id": "mp-2", "formula": "MgO", "gap pbe": 4.5, "desc": [1.5, 2.0, -3.25e-4], "text": 'quote " and ] bracket'},
        {"id": "mp-3", "formula": "ZnS", "gap pbe": 0.0, "nested": [[], {}, [{"a": "x,y"}]]},
    ]
    path = tmp_path / "records.json"
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    # tiny chunks force every element to be split across reads
    assert list(iter_json_array(path, chunk_chars=7)) == records
    assert list(iter_json_array(path)) == records


def test_handles_empty_array(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("[ ]", encoding="utf-8")
    assert list(iter_json_array(path, chunk_chars=2)) == []
