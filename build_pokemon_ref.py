#!/usr/bin/env python3
"""Build a compact pokemon_ref.json from the raw data files."""

import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE, "pokemon_ref.json")

JS_FILES = [
    ("abilities", "abilities.js", "BattleAbilities"),
    ("items", "items.js", "BattleItems"),
    ("learnsets", "learnsets.js", "BattleLearnsets"),
    ("pokedex", "pokedex.js", "BattlePokedex"),
    ("typechart", "typechart.js", "BattleTypeChart"),
]

JSON_FILES = [
    ("moves", "moves.json"),
    ("teams", "gen9ou.json"),
]

STATS_FILE = "gen9ou-1825.json"
MIN_THRESHOLD = 0.001
DECIMAL_PLACES = 4


def parse_js_export(filepath, var_name):
    """Parse a JS file with `exports.<var_name> = {...}` into a dict."""
    with open(filepath) as f:
        content = f.read()
    prefix = f"exports.{var_name} = "
    obj_str = content[len(prefix):]
    if obj_str.endswith(";"):
        obj_str = obj_str[:-1]
    # Quote bare keys: identifiers after { or , and before :
    quoted = re.sub(r'(?<=[{,])([a-zA-Z_]\w*)(?=:)', r'"\1"', obj_str)
    return json.loads(quoted)


def compress_value(obj):
    """Recursively round floats and drop near-zero float entries from dicts."""
    if isinstance(obj, dict):
        return {
            k: compress_value(v)
            for k, v in obj.items()
            if not (isinstance(v, float) and abs(v) < MIN_THRESHOLD)
        }
    if isinstance(obj, float):
        return round(obj, DECIMAL_PLACES)
    if isinstance(obj, list):
        return [compress_value(x) for x in obj]
    return obj


def load_stats(filepath):
    """Load and compress the stats JSON file."""
    with open(filepath) as f:
        data = json.load(f)
    data["data"] = compress_value(data["data"])
    return data


def main():
    result = {}

    for key, filename, var_name in JS_FILES:
        path = os.path.join(BASE, filename)
        result[key] = parse_js_export(path, var_name)
        print(f"  Loaded {filename}: {len(result[key])} entries")

    for key, filename in JSON_FILES:
        path = os.path.join(BASE, filename)
        with open(path) as f:
            result[key] = json.load(f)
        print(f"  Loaded {filename}")

    path = os.path.join(BASE, STATS_FILE)
    result["stats"] = load_stats(path)
    print(f"  Loaded {STATS_FILE} (compressed): {len(result['stats']['data'])} pokemon")

    with open(OUTPUT, "w") as f:
        json.dump(result, f, separators=(",", ":"))

    size_mb = os.path.getsize(OUTPUT) / 1024 / 1024
    print(f"\n  Written {OUTPUT}")
    print(f"  Size: {size_mb:.2f} MB")


if __name__ == "__main__":
    print("Building pokemon_ref.json...")
    main()
    print("Done.")
