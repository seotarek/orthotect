#!/usr/bin/env python3
"""
Orthotect UI/UX Knowledge Search Engine
Fast, offline, dependency-free local search module for Orthotect's design intelligence.
Indexes style recipes, semantic palettes, typographic scales, component contracts,
and accessibility matrices with relevance ranking, schema validation, and provenance reporting.
"""

import json
import os
import sys
import re
import argparse
from pathlib import Path

# Resolve base paths
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
DEFAULT_KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
DEFAULT_SCHEMAS_DIR = DEFAULT_KNOWLEDGE_DIR / "schemas"

def tokenize(text):
    """Normalize and tokenize text into lowercase word tokens."""
    if not text:
        return []
    if isinstance(text, list):
        text = " ".join(str(x) for x in text)
    elif isinstance(text, dict):
        text = " ".join(str(v) for v in text.values())
    tokens = re.findall(r'[a-zA-Z0-9_\-]+', str(text).lower())
    return tokens

def load_knowledge_base(knowledge_dir=None):
    """
    Loads all knowledge records and style recipes from knowledge_dir.
    Returns a list of standardized record dictionaries.
    """
    kb_path = Path(knowledge_dir) if knowledge_dir else DEFAULT_KNOWLEDGE_DIR
    if not kb_path.exists():
        return []

    records = []
    
    for root, dirs, files in os.walk(kb_path):
        # Skip schemas directory
        if "schemas" in Path(root).parts:
            continue
            
        for file in files:
            if not file.endswith(".json"):
                continue
            file_path = Path(root) / file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Normalize style recipes vs standard knowledge records
                rel_path = file_path.relative_to(kb_path)
                category = rel_path.parts[0] if len(rel_path.parts) > 1 else "general"
                
                if "designThesis" in data:
                    # Style recipe
                    record = {
                        "id": data.get("id", file_path.stem),
                        "title": data.get("name", file_path.stem),
                        "category": "styles",
                        "summary": data.get("designThesis", ""),
                        "whenToUse": " | ".join(data.get("bestFitContexts", [])),
                        "whenNotToUse": " | ".join(data.get("poorFitContexts", [])),
                        "rules": [
                            f"Color: {data.get('colorStrategy', {}).get('canvasTone', '')}",
                            f"Accent: {data.get('colorStrategy', {}).get('accentUsage', '')}",
                            f"Typography: {data.get('typographyStrategy', {}).get('fontPairing', '')}",
                            f"Density: {data.get('layoutRhythm', {}).get('density', '')}",
                            f"Primary Action: {data.get('componentGuidelines', {}).get('primaryActionStyle', '')}"
                        ],
                        "antiPatterns": data.get("antiPatterns", []),
                        "applicableStacks": ["universal", "css", "tailwind", "react", "html"],
                        "accessibilityNotes": f"Target WCAG: {data.get('accessibilityProfile', {}).get('targetWcagRatio', 4.5)}:1. Keyboard: {data.get('accessibilityProfile', {}).get('keyboardHandling', '')}",
                        "provenance": f"Orthotect Style Recipe v{data.get('version', '1.0.0')}",
                        "verificationStatus": "VERIFIED_DETERMINISTIC",
                        "tags": ["style-recipe", "design-system", data.get("layoutRhythm", {}).get("density", "default")] + data.get("bestFitContexts", []),
                        "raw": data,
                        "_source": str(rel_path),
                        "_type": "style-recipe"
                    }
                else:
                    # Knowledge record
                    record = dict(data)
                    record["_source"] = str(rel_path)
                    record["_type"] = "knowledge-record"
                    if "category" not in record:
                        record["category"] = category
                
                records.append(record)
            except Exception as e:
                # Malformed file handled gracefully
                continue
                
    return records

def calculate_relevance(record, query_tokens):
    """
    Computes a weighted relevance score for a record given query tokens.
    Title matches: 5x
    Tag matches: 3x
    Summary / thesis matches: 2x
    Rules / anti-patterns matches: 1x
    """
    if not query_tokens:
        return 1.0

    score = 0.0
    title_tokens = set(tokenize(record.get("title", "")))
    id_tokens = set(tokenize(record.get("id", "")))
    tags_tokens = set(tokenize(record.get("tags", [])))
    summary_tokens = set(tokenize(record.get("summary", "")))
    rules_tokens = set(tokenize(record.get("rules", [])))
    anti_tokens = set(tokenize(record.get("antiPatterns", [])))

    for qt in query_tokens:
        if qt in title_tokens or qt in id_tokens:
            score += 5.0
        if qt in tags_tokens:
            score += 3.0
        if qt in summary_tokens:
            score += 2.0
        if qt in rules_tokens or qt in anti_tokens:
            score += 1.0

    return score

def search_knowledge(query=None, category=None, tag=None, stack=None, limit=10, knowledge_dir=None):
    """
    Searches the knowledge base with filtering and relevance ranking.
    """
    records = load_knowledge_base(knowledge_dir)
    query_tokens = tokenize(query) if query else []
    
    results = []
    for r in records:
        # Category filter
        if category and r.get("category", "").lower() != category.lower():
            continue
            
        # Tag filter
        if tag:
            record_tags = [str(t).lower() for t in r.get("tags", [])]
            if tag.lower() not in record_tags:
                continue
                
        # Stack filter
        if stack:
            record_stacks = [str(s).lower() for s in r.get("applicableStacks", [])]
            if stack.lower() not in record_stacks and "universal" not in record_stacks:
                continue
                
        score = calculate_relevance(r, query_tokens)
        if query_tokens and score <= 0.0:
            continue
            
        results.append({
            "score": score,
            "id": r.get("id"),
            "title": r.get("title"),
            "category": r.get("category"),
            "summary": r.get("summary"),
            "rules": r.get("rules", []),
            "antiPatterns": r.get("antiPatterns", []),
            "applicableStacks": r.get("applicableStacks", []),
            "accessibilityNotes": r.get("accessibilityNotes", ""),
            "provenance": r.get("provenance", ""),
            "verificationStatus": r.get("verificationStatus", "HEURISTIC"),
            "tags": r.get("tags", []),
            "source": r.get("_source"),
            "type": r.get("_type")
        })

    # Sort descending by score, then alphabetically by title
    results.sort(key=lambda x: (-x["score"], x["title"]))
    return results[:limit]

def _validate_schema_builtin(data, schema):
    """
    Lightweight, dependency-free schema validator for Orthotect records & recipes.
    Validates required fields, types, and enums against JSON Schema definitions.
    """
    errors = []
    for req in schema.get("required", []):
        if req not in data:
            errors.append(f"Missing required property: '{req}'")
        else:
            prop_def = schema.get("properties", {}).get(req, {})
            val = data[req]
            expected_type = prop_def.get("type")
            if expected_type == "string" and not isinstance(val, str):
                errors.append(f"Property '{req}' must be a string, got {type(val).__name__}")
            elif expected_type == "number" and not isinstance(val, (int, float)):
                errors.append(f"Property '{req}' must be a number, got {type(val).__name__}")
            elif expected_type == "integer" and not isinstance(val, int):
                errors.append(f"Property '{req}' must be an integer, got {type(val).__name__}")
            elif expected_type == "boolean" and not isinstance(val, bool):
                errors.append(f"Property '{req}' must be a boolean, got {type(val).__name__}")
            elif expected_type == "array" and not isinstance(val, list):
                errors.append(f"Property '{req}' must be an array, got {type(val).__name__}")
            elif expected_type == "object" and not isinstance(val, dict):
                errors.append(f"Property '{req}' must be an object, got {type(val).__name__}")

            if "enum" in prop_def and val not in prop_def["enum"]:
                errors.append(f"Property '{req}' value '{val}' not in allowed enum: {prop_def['enum']}")

            if expected_type == "object" and isinstance(val, dict):
                for sub_req in prop_def.get("required", []):
                    if sub_req not in val:
                        errors.append(f"Missing required sub-property '{req}.{sub_req}'")
    return errors

def validate_knowledge_base(knowledge_dir=None, schemas_dir=None):
    """
    Validates all files against their respective JSON schemas.
    Uses jsonschema if installed; falls back to pure standard-library validation otherwise.
    Returns (bool success, list messages).
    """
    has_jsonschema = False
    try:
        import jsonschema
        has_jsonschema = True
    except ImportError:
        has_jsonschema = False

    kb_path = Path(knowledge_dir) if knowledge_dir else DEFAULT_KNOWLEDGE_DIR
    sc_path = Path(schemas_dir) if schemas_dir else DEFAULT_SCHEMAS_DIR

    recipe_schema_file = sc_path / "style-recipe.schema.json"
    record_schema_file = sc_path / "knowledge-record.schema.json"

    if not recipe_schema_file.exists() or not record_schema_file.exists():
        return False, ["Missing required schema definitions in schemas directory"]

    with open(recipe_schema_file, "r", encoding="utf-8") as f:
        recipe_schema = json.load(f)
    with open(record_schema_file, "r", encoding="utf-8") as f:
        record_schema = json.load(f)

    errors = []
    validated_count = 0

    for root, dirs, files in os.walk(kb_path):
        if "schemas" in Path(root).parts:
            continue
        for file in files:
            if not file.endswith(".json"):
                continue
            file_path = Path(root) / file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                target_schema = recipe_schema if "designThesis" in data else record_schema
                if has_jsonschema:
                    jsonschema.validate(instance=data, schema=target_schema)
                else:
                    item_errors = _validate_schema_builtin(data, target_schema)
                    if item_errors:
                        errors.extend([f"{file_path.name}: {err}" for err in item_errors])
                validated_count += 1
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")

    if errors:
        return False, errors
    engine_mode = "jsonschema" if has_jsonschema else "standard-library"
    return True, [f"Successfully validated {validated_count} knowledge records & style recipes ({engine_mode})."]

def main():
    parser = argparse.ArgumentParser(
        description="Orthotect UI/UX Knowledge Search Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("query", nargs="?", default=None, help="Search terms / query")
    parser.add_argument("-c", "--category", help="Filter by category (styles, palettes, typography, components, patterns, ux-guidelines, accessibility, motion, bidi)")
    parser.add_argument("-t", "--tag", help="Filter by tag (e.g. contrast, bidi, fsm, keyboard)")
    parser.add_argument("-s", "--stack", help="Filter by stack (e.g. css, react, tailwind, html)")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Maximum number of results (default: 10)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--validate", action="store_true", help="Validate all records against schemas")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show full rules and anti-patterns")

    args = parser.parse_args()

    if args.validate:
        success, messages = validate_knowledge_base()
        if args.json:
            print(json.dumps({"valid": success, "messages": messages}, indent=2))
        else:
            if success:
                print(f"[OK] {messages[0]}")
            else:
                print("[ERROR] Schema validation failed:")
                for m in messages:
                    print(f"  • {m}")
        sys.exit(0 if success else 1)

    results = search_knowledge(
        query=args.query,
        category=args.category,
        tag=args.tag,
        stack=args.stack,
        limit=args.limit
    )

    if args.json:
        print(json.dumps(results, indent=2))
        return

    # High-contrast ASCII terminal output
    print("╔═════════════════════════════════════════════════════════════════════════════╗")
    print("║               ORTHOTECT UI/UX KNOWLEDGE SEARCH ENGINE                       ║")
    print("╚═════════════════════════════════════════════════════════════════════════════╝\n")
    
    filter_desc = []
    if args.query: filter_desc.append(f"Query: '{args.query}'")
    if args.category: filter_desc.append(f"Category: {args.category}")
    if args.tag: filter_desc.append(f"Tag: {args.tag}")
    if args.stack: filter_desc.append(f"Stack: {args.stack}")
    
    if filter_desc:
        print(f"Filters: {' | '.join(filter_desc)}")
    print(f"Found {len(results)} matching records (Limit: {args.limit}):\n")

    if not results:
        print("  ⚠️ No matching knowledge records found. Try broader search terms or check category name.")
        return

    for i, res in enumerate(results, 1):
        status_symbol = "[VERIFIED]" if "VERIFIED" in res["verificationStatus"] else "[HEURISTIC]"
        print(f"{i}. {res['title']} ({res['category']}) {status_symbol}")
        print(f"   ID: {res['id']} | Source: {res['source']}")
        print(f"   Summary: {res['summary']}")
        print(f"   Tags: {', '.join(res['tags'][:6])}")
        
        if args.verbose:
            if res.get("rules"):
                print("   Rules:")
                for rule in res["rules"][:4]:
                    print(f"     • {rule}")
            if res.get("antiPatterns"):
                print("   Anti-Patterns:")
                for ap in res["antiPatterns"][:3]:
                    print(f"     ✖ {ap}")
        print()

if __name__ == "__main__":
    main()
