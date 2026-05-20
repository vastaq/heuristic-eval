"""Small bridge to the repository's Node `yaml` package.

Python keeps the testset scripts easy to run with the standard library. The
workspace already has the `yaml` npm package through promptfoo dependencies, so
we use Node only for YAML parsing/stringifying instead of adding a Python
dependency.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any


def parse_yaml(text: str) -> Any:
    script = """
const YAML = require('yaml');
const fs = require('fs');
const input = fs.readFileSync(0, 'utf8');
const parsed = YAML.parse(input);
process.stdout.write(JSON.stringify(parsed ?? null));
"""
    result = subprocess.run(
        ["node", "-e", script],
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip())
    return json.loads(result.stdout)


def dump_yaml(value: Any) -> str:
    script = """
const YAML = require('yaml');
const fs = require('fs');
const input = fs.readFileSync(0, 'utf8');
const value = JSON.parse(input);
process.stdout.write(YAML.stringify(value, { lineWidth: 0 }));
"""
    result = subprocess.run(
        ["node", "-e", script],
        input=json.dumps(value, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip())
    return result.stdout
