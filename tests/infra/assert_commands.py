import json
import subprocess
import shutil
import pathlib
import pytest

JSON_PATH = pathlib.Path(__file__).parent / "test_cases.json"
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

test_cases = data["test_cases"]

def pytest_generate_tests(metafunc):
    if "test_case" in metafunc.fixturenames:
        metafunc.parametrize(
            "test_case", 
            test_cases, 
            ids=[tc["name"] for tc in test_cases]
        )

def test_dns_scenario(test_case):
    required_tool = test_case.get("requires_tool")
    if required_tool and shutil.which(required_tool) is None:
        pytest.skip(f"Missing tool : '{required_tool}' is not installed on this system")

    result = subprocess.run(
        test_case["command"],
        capture_output=True,
        text=True,
        check=False
    )
    output = result.stdout + result.stderr

    for expected in test_case["expected_strings"]:
        assert expected in output, (
            f"\n--- TEST FAIL : {test_case['name']} ---\n"
            f"Command : {' '.join(test_case['command'])}\n"
            f"Missing entry : '{expected}'\n"
            f"Output :\n{output}\n"
            f"---------------------------------------"
        )
