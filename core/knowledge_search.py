#!/usr/bin/env python3
"""
Orthotect UI/UX Knowledge Search Engine & Schema Verification Platform
Fast, deterministic, offline local search engine and schema validator for Orthotect design intelligence.
Implements:
  1. Full recursive JSON Schema validation with boolean type-safety, unsupported keyword detection, and honest diagnostics.
  2. Multi-field BM25 relevance ranking with corpus IDF, document length normalization, and score explanations.
  3. Unicode word tokenization supporting English and Arabic normalization.
  4. Evidence-based verification status derivation (NOT_EVALUATED, HEURISTIC, VERIFIED_DETERMINISTIC, VERIFIED_BROWSER).
  5. Search quality benchmark suite computing Precision@K, Recall@K, and Mean Reciprocal Rank (MRR).
"""

import json
import os
import sys
import re
import math
import argparse
from pathlib import Path

# Resolve base paths
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
DEFAULT_KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
DEFAULT_SCHEMAS_DIR = DEFAULT_KNOWLEDGE_DIR / "schemas"
DEFAULT_BENCHMARK_PATH = DEFAULT_KNOWLEDGE_DIR / "benchmarks" / "search_benchmark.json"

ARABIC_DIACRITICS = re.compile(r"[ً-ٰٟ]")

def normalize_text(text):
    """Normalize English and Arabic text strings."""
    if not text:
        return ""
    if isinstance(text, list):
        text = " ".join(str(x) for x in text)
    elif isinstance(text, dict):
        text = " ".join(str(v) for v in text.values())
    s = str(text).lower()
    # Remove Arabic tashkeel (diacritics)
    s = ARABIC_DIACRITICS.sub("", s)
    # Normalize Alef variants (أ, إ, آ -> ا)
    s = re.sub(r"[إأآ]", "ا", s)
    # Normalize Teh Marbuta (ة -> ه)
    s = re.sub(r"ة", "ه", s)
    return s

def tokenize(text):
    """Normalize and tokenize text into lowercase word tokens supporting Unicode and Arabic."""
    norm = normalize_text(text)
    if not norm:
        return []
    return re.findall(r"[\w\-]+", norm, re.UNICODE)

def derive_verification_status(data, evidence=None):
    """
    Derives verification status strictly based on verifiable evidence.
    Evidence dimensions:
      - schemaValid (bool)
      - gatesPassed (list of string gate names)
      - browserVerified (bool)
    Returns:
      - VERIFIED_BROWSER if real browser execution is recorded
      - VERIFIED_DETERMINISTIC if deterministic gates passed
      - HEURISTIC for advisory guidance without gate certifications
      - NOT_EVALUATED if unverified / evidence absent
    """
    ev = evidence or data.get("evidence", {})
    if not isinstance(ev, dict):
        ev = {}

    if ev.get("browserVerified") is True:
        return "VERIFIED_BROWSER"
    
    gates = ev.get("gatesPassed", [])
    if isinstance(gates, list) and len(gates) >= 1:
        return "VERIFIED_DETERMINISTIC"

    if ev.get("heuristic") is True or data.get("verificationStatus") == "HEURISTIC":
        return "HEURISTIC"

    if data.get("verificationStatus") == "NOT_EVALUATED":
        return "NOT_EVALUATED"

    # In absence of recorded evidence, default to NOT_EVALUATED
    return "NOT_EVALUATED"


def load_knowledge_base(knowledge_dir=None, return_errors=False):
    """
    Loads all knowledge records and style recipes from knowledge_dir.
    Returns list of records, and optionally a list of parse/load error diagnostics.
    """
    kb_path = Path(knowledge_dir) if knowledge_dir else DEFAULT_KNOWLEDGE_DIR
    if not kb_path.exists():
        return ([], ["Knowledge directory not found"]) if return_errors else []

    records = []
    load_errors = []

    for root, dirs, files in os.walk(kb_path):
        if "schemas" in Path(root).parts or "benchmarks" in Path(root).parts:
            continue
            
        for file in sorted(files):
            if not file.endswith(".json"):
                continue
            file_path = Path(root) / file
            rel_path = file_path.relative_to(kb_path)
            category = rel_path.parts[0] if len(rel_path.parts) > 1 else "general"

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                load_errors.append(f"{file_path.name}: Malformed JSON syntax: {e}")
                continue

            if not isinstance(data, dict):
                load_errors.append(f"{file_path.name}: Root JSON document must be an object, got {type(data).__name__}")
                continue

            if "designThesis" in data:
                # Style recipe
                status = derive_verification_status(data, data.get("evidence"))
                record = {
                    "id": data.get("id", file_path.stem),
                    "title": data.get("name", file_path.stem),
                    "category": "styles",
                    "summary": data.get("designThesis", ""),
                    "whenToUse": " | ".join(data.get("bestFitContexts", [])),
                    "whenNotToUse": " | ".join(data.get("poorFitContexts", [])),
                    "rules": [
                        f"Color: {data.get("colorStrategy", {}).get("canvasTone", "")}",
                        f"Accent: {data.get("colorStrategy", {}).get("accentUsage", "")}",
                        f"Typography: {data.get("typographyStrategy", {}).get("fontPairing", "")}",
                        f"Density: {data.get("layoutRhythm", {}).get("density", "")}",
                        f"Primary Action: {data.get("componentGuidelines", {}).get("primaryActionStyle", "")}"
                    ],
                    "antiPatterns": data.get("antiPatterns", []),
                    "applicableStacks": ["universal", "css", "tailwind", "react", "html"],
                    "accessibilityNotes": f"Target WCAG: {data.get("accessibilityProfile", {}).get("targetWcagRatio", 4.5)}:1. Keyboard: {data.get("accessibilityProfile", {}).get("keyboardHandling", "")}",
                    "provenance": f"Orthotect Style Recipe v{data.get("version", "1.0.0")}",
                    "verificationStatus": status,
                    "evidence": data.get("evidence", {}),
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
                record["verificationStatus"] = derive_verification_status(data, data.get("evidence"))
            
            records.append(record)

    if return_errors:
        return records, load_errors
    return records

def calculate_bm25_scores(records, query_tokens, k1=1.2, b=0.75):
    """
    Computes deterministic BM25 scores with document length normalization and corpus IDF.
    Field weighting:
      title / id: 5.0
      tags: 3.0
      summary / thesis: 2.0
      rules / antiPatterns: 1.0
    """
    if not query_tokens:
        return {id(r): (1.0, {}) for r in records}

    N = len(records)
    if N == 0:
        return {}

    doc_data = {}
    total_dl = 0

    for r in records:
        r_id = id(r)
        title_toks = tokenize(r.get("title", "")) + tokenize(r.get("id", ""))
        tags_toks = tokenize(r.get("tags", []))
        summary_toks = tokenize(r.get("summary", ""))
        rules_toks = tokenize(r.get("rules", [])) + tokenize(r.get("antiPatterns", []))

        # Field weighted term frequency
        tf = {}
        for t in title_toks:
            tf[t] = tf.get(t, 0.0) + 5.0
        for t in tags_toks:
            tf[t] = tf.get(t, 0.0) + 3.0
        for t in summary_toks:
            tf[t] = tf.get(t, 0.0) + 2.0
        for t in rules_toks:
            tf[t] = tf.get(t, 0.0) + 1.0

        dl = len(title_toks) + len(tags_toks) + len(summary_toks) + len(rules_toks)
        doc_data[r_id] = {"tf": tf, "dl": dl}
        total_dl += dl

    avgdl = total_dl / N if N > 0 else 1.0

    # Corpus IDF for each query term
    idf = {}
    for qt in query_tokens:
        df = sum(1 for d in doc_data.values() if d["tf"].get(qt, 0) > 0)
        idf[qt] = math.log(((N - df + 0.5) / (df + 0.5)) + 1.0)

    scores = {}
    for r in records:
        r_id = id(r)
        d = doc_data[r_id]
        dl = d["dl"]
        score = 0.0
        explanation = {}

        for qt in query_tokens:
            q_tf = d["tf"].get(qt, 0.0)
            if q_tf > 0:
                q_idf = idf[qt]
                numerator = q_tf * (k1 + 1.0)
                denominator = q_tf + k1 * (1.0 - b + b * (dl / avgdl if avgdl > 0 else 1.0))
                contrib = q_idf * (numerator / denominator)
                score += contrib
                explanation[qt] = {
                    "tf": round(q_tf, 2),
                    "idf": round(q_idf, 4),
                    "contrib": round(contrib, 4)
                }

        scores[r_id] = (round(score, 4), explanation)

    return scores

def calculate_relevance(record, query_tokens):
    """
    Computes relevance score for a single record given query tokens.
    Maintains compatibility with unit tests.
    """
    if not query_tokens:
        return 1.0

    title_tokens = set(tokenize(record.get("title", "")) + tokenize(record.get("id", "")))
    tags_tokens = set(tokenize(record.get("tags", [])))
    summary_tokens = set(tokenize(record.get("summary", "")))
    rules_tokens = set(tokenize(record.get("rules", [])) + tokenize(record.get("antiPatterns", [])))

    score = 0.0
    for qt in query_tokens:
        if qt in title_tokens:
            score += 5.0
        if qt in tags_tokens:
            score += 3.0
        if qt in summary_tokens:
            score += 2.0
        if qt in rules_tokens:
            score += 1.0

    return score

def search_knowledge(query=None, category=None, tag=None, stack=None, limit=10, knowledge_dir=None):
    """
    Searches the knowledge base with BM25 relevance ranking and filtering.
    """
    records = load_knowledge_base(knowledge_dir)
    query_tokens = tokenize(query) if query else []
    
    # Pre-filter by metadata
    filtered_records = []
    for r in records:
        if category and r.get("category", "").lower() != category.lower():
            continue
        if tag:
            record_tags = [str(t).lower() for t in r.get("tags", [])]
            if tag.lower() not in record_tags:
                continue
        if stack:
            record_stacks = [str(s).lower() for s in r.get("applicableStacks", [])]
            if stack.lower() not in record_stacks and "universal" not in record_stacks:
                continue
        filtered_records.append(r)

    # Compute BM25 scores
    bm25_scores = calculate_bm25_scores(filtered_records, query_tokens)
    
    results = []
    for r in filtered_records:
        score, explanation = bm25_scores.get(id(r), (0.0, {}))
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
            "verificationStatus": r.get("verificationStatus", "NOT_EVALUATED"),
            "evidence": r.get("evidence", {}),
            "tags": r.get("tags", []),
            "source": r.get("_source"),
            "type": r.get("_type"),
            "_score_explanation": explanation
        })

    # Deterministic sort: descending by BM25 score, then alphabetically by title
    results.sort(key=lambda x: (-x["score"], x["title"]))
    return results[:limit]

SUPPORTED_SCHEMA_KEYWORDS = {
    "$schema", "title", "description", "type", "required", "properties",
    "items", "enum", "additionalProperties", "minimum", "maximum", "minLength", "maxLength", "pattern"
}

def _validate_schema_builtin(data, schema, path="root", strict_mode=True):
    """
    Recursive, dependency-free schema validator for Orthotect records & recipes.
    Strictly validates root types, nested properties, array items, enums, required fields,
    regex patterns, string lengths, numeric ranges, and additionalProperties restrictions.
    Fails closed on unsupported schema keywords or type violations.
    """
    errors = []

    # 1. Unsupported keyword check in strict mode
    if strict_mode and isinstance(schema, dict):
        unsupported = set(schema.keys()) - SUPPORTED_SCHEMA_KEYWORDS
        if unsupported:
            errors.append(f"{path}: Unsupported schema keyword(s) in strict fallback mode: {sorted(list(unsupported))}")
            return errors

    # 2. Root data type validation
    expected_root_type = schema.get("type") if isinstance(schema, dict) else None
    if expected_root_type:
        if expected_root_type == "object" and (not isinstance(data, dict) or data is None):
            errors.append(f"{path}: Expected object, got {type(data).__name__ if data is not None else 'null'}")
            return errors
        elif expected_root_type == "array" and (not isinstance(data, list) or data is None):
            errors.append(f"{path}: Expected array, got {type(data).__name__ if data is not None else 'null'}")
            return errors
        elif expected_root_type == "string" and not isinstance(data, str):
            errors.append(f"{path}: Expected string, got {type(data).__name__}")
            return errors
        elif expected_root_type == "number" and (not isinstance(data, (int, float)) or isinstance(data, bool)):
            errors.append(f"{path}: Expected number, got {type(data).__name__}")
            return errors
        elif expected_root_type == "integer" and (not isinstance(data, int) or isinstance(data, bool)):
            errors.append(f"{path}: Expected integer, got {type(data).__name__}")
            return errors
        elif expected_root_type == "boolean" and not isinstance(data, bool):
            errors.append(f"{path}: Expected boolean, got {type(data).__name__}")
            return errors

    # 3. Object properties, required fields, and additionalProperties recursive check
    if isinstance(data, dict) and isinstance(schema, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Additional properties check if forbidden
        if schema.get("additionalProperties") is False:
            extra_props = set(data.keys()) - set(properties.keys())
            for extra in sorted(list(extra_props)):
                errors.append(f"{path}: Additional property '{extra}' is not allowed")

        # Check required fields
        for req in required:
            if req not in data:
                errors.append(f"{path}: Missing required property: '{req}'")

        # Recursively validate every present property
        for prop_name, prop_val in data.items():
            if prop_name in properties:
                prop_schema = properties[prop_name]
                prop_path = f"{path}.{prop_name}" if path != "root" else prop_name
                prop_type = prop_schema.get("type")

                # Strict type checks preventing bool inheritance issues
                if prop_type == "string":
                    if not isinstance(prop_val, str):
                        errors.append(f"{prop_path}: Property '{prop_name}' must be a string, got {type(prop_val).__name__}")
                    else:
                        if "minLength" in prop_schema and len(prop_val) < prop_schema["minLength"]:
                            errors.append(f"{prop_path}: Property '{prop_name}' string too short (length {len(prop_val)} < {prop_schema['minLength']})")
                        if "maxLength" in prop_schema and len(prop_val) > prop_schema["maxLength"]:
                            errors.append(f"{prop_path}: Property '{prop_name}' string too long (length {len(prop_val)} > {prop_schema['maxLength']})")
                        if "pattern" in prop_schema:
                            try:
                                if not re.search(prop_schema["pattern"], prop_val):
                                    errors.append(f"{prop_path}: Property '{prop_name}' value '{prop_val}' does not match pattern '{prop_schema['pattern']}'")
                            except Exception as re_err:
                                errors.append(f"{prop_path}: Invalid regex pattern '{prop_schema['pattern']}': {re_err}")
                elif prop_type == "number":
                    if not isinstance(prop_val, (int, float)) or isinstance(prop_val, bool):
                        errors.append(f"{prop_path}: Property '{prop_name}' must be a number, got {type(prop_val).__name__}")
                    else:
                        if "minimum" in prop_schema and prop_val < prop_schema["minimum"]:
                            errors.append(f"{prop_path}: Property '{prop_name}' number {prop_val} < minimum {prop_schema['minimum']}")
                        if "maximum" in prop_schema and prop_val > prop_schema["maximum"]:
                            errors.append(f"{prop_path}: Property '{prop_name}' number {prop_val} > maximum {prop_schema['maximum']}")
                elif prop_type == "integer":
                    if not isinstance(prop_val, int) or isinstance(prop_val, bool):
                        errors.append(f"{prop_path}: Property '{prop_name}' must be an integer, got {type(prop_val).__name__}")
                    else:
                        if "minimum" in prop_schema and prop_val < prop_schema["minimum"]:
                            errors.append(f"{prop_path}: Property '{prop_name}' integer {prop_val} < minimum {prop_schema['minimum']}")
                        if "maximum" in prop_schema and prop_val > prop_schema["maximum"]:
                            errors.append(f"{prop_path}: Property '{prop_name}' integer {prop_val} > maximum {prop_schema['maximum']}")
                elif prop_type == "boolean" and not isinstance(prop_val, bool):
                    errors.append(f"{prop_path}: Property '{prop_name}' must be a boolean, got {type(prop_val).__name__}")
                elif prop_type == "array":
                    if not isinstance(prop_val, list):
                        errors.append(f"{prop_path}: Property '{prop_name}' must be an array, got {type(prop_val).__name__}")
                    else:
                        items_schema = prop_schema.get("items")
                        if items_schema:
                            for idx, item in enumerate(prop_val):
                                item_path = f"{prop_path}[{idx}]"
                                sub_errs = _validate_schema_builtin(item, items_schema, path=item_path, strict_mode=strict_mode)
                                errors.extend(sub_errs)
                elif prop_type == "object":
                    if not isinstance(prop_val, dict):
                        errors.append(f"{prop_path}: Property '{prop_name}' must be an object, got {type(prop_val).__name__}")
                    else:
                        sub_errs = _validate_schema_builtin(prop_val, prop_schema, path=prop_path, strict_mode=strict_mode)
                        errors.extend(sub_errs)

                # Enum validation
                if "enum" in prop_schema and prop_val not in prop_schema["enum"]:
                    errors.append(f"{prop_path}: Property '{prop_name}' value '{prop_val}' not in allowed enum: {prop_schema['enum']}")


    return errors

def validate_knowledge_base(knowledge_dir=None, schemas_dir=None, force_fallback=False):
    """
    Validates all files against their respective JSON schemas.
    Uses jsonschema if installed and not force_fallback; falls back to pure standard-library validation.
    Returns (bool success, list messages).
    """
    has_jsonschema = False
    if not force_fallback:
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

    try:
        with open(recipe_schema_file, "r", encoding="utf-8") as f:
            recipe_schema = json.load(f)
        with open(record_schema_file, "r", encoding="utf-8") as f:
            record_schema = json.load(f)
    except Exception as e:
        return False, [f"Failed to load schema file: {e}"]

    errors = []
    validated_count = 0

    for root, dirs, files in os.walk(kb_path):
        if "schemas" in Path(root).parts or "benchmarks" in Path(root).parts:
            continue
        for file in sorted(files):
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
                    item_errors = _validate_schema_builtin(data, target_schema, strict_mode=True)
                    if item_errors:
                        errors.extend([f"{file_path.name}: {err}" for err in item_errors])
                validated_count += 1
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")

    if errors:
        return False, errors
    engine_mode = "jsonschema" if has_jsonschema else "standard-library fallback"
    return True, [f"Successfully validated {validated_count} knowledge records & style recipes ({engine_mode})."]

def run_search_benchmark(benchmark_path=None, knowledge_dir=None):
    """
    Executes search benchmark evaluation measuring:
      - Precision@1, Precision@3, Precision@5
      - Recall@3, Recall@5
      - Mean Reciprocal Rank (MRR)
    """
    bench_file = Path(benchmark_path) if benchmark_path else DEFAULT_BENCHMARK_PATH
    if not bench_file.exists():
        raise FileNotFoundError(f"Benchmark dataset not found at: {bench_file}")

    with open(bench_file, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    total_queries = len(benchmarks)
    if total_queries == 0:
        return {"total_queries": 0, "mrr": 0.0, "p_at_1": 0.0, "p_at_3": 0.0, "r_at_3": 0.0}

    rr_sum = 0.0
    p1_sum = 0.0
    p3_sum = 0.0
    p5_sum = 0.0
    r3_sum = 0.0
    r5_sum = 0.0

    query_details = []

    for b in benchmarks:
        q_id = b["id"]
        q_text = b["query"]
        expected = set(b.get("expected_ids", []))
        category = b.get("category")
        tag = b.get("tag")
        stack = b.get("stack")

        results = search_knowledge(
            query=q_text,
            category=category,
            tag=tag,
            stack=stack,
            limit=10,
            knowledge_dir=knowledge_dir
        )
        result_ids = [r["id"] for r in results]

        # Calculate Reciprocal Rank
        rr = 0.0
        for rank, res_id in enumerate(result_ids, 1):
            if res_id in expected:
                rr = 1.0 / rank
                break
        rr_sum += rr

        # Precision & Recall at K
        def p_at_k(k):
            top_k = set(result_ids[:k])
            hits = len(top_k.intersection(expected))
            return hits / k if k > 0 else 0.0

        def r_at_k(k):
            top_k = set(result_ids[:k])
            hits = len(top_k.intersection(expected))
            return hits / len(expected) if expected else 0.0

        p1 = p_at_k(1)
        p3 = p_at_k(3)
        p5 = p_at_k(5)
        r3 = r_at_k(3)
        r5 = r_at_k(5)

        p1_sum += p1
        p3_sum += p3
        p5_sum += p5
        r3_sum += r3
        r5_sum += r5

        query_details.append({
            "id": q_id,
            "query": q_text,
            "expected": list(expected),
            "retrieved": result_ids[:5],
            "rr": round(rr, 4),
            "p@3": round(p3, 4),
            "r@3": round(r3, 4)
        })

    metrics = {
        "total_queries": total_queries,
        "mrr": round(rr_sum / total_queries, 4),
        "precision_at_1": round(p1_sum / total_queries, 4),
        "precision_at_3": round(p3_sum / total_queries, 4),
        "precision_at_5": round(p5_sum / total_queries, 4),
        "recall_at_3": round(r3_sum / total_queries, 4),
        "recall_at_5": round(r5_sum / total_queries, 4),
        "details": query_details
    }
    return metrics

def main():
    parser = argparse.ArgumentParser(
        description="Orthotect UI/UX Knowledge Search Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("query", nargs="?", default=None, help="Search terms / query")
    parser.add_argument("-c", "--category", help="Filter by category")
    parser.add_argument("-t", "--tag", help="Filter by tag")
    parser.add_argument("-s", "--stack", help="Filter by stack")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Maximum number of results (default: 10)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--validate", action="store_true", help="Validate all records against schemas")
    parser.add_argument("--fallback", action="store_true", help="Force pure standard-library fallback validator")
    parser.add_argument("--benchmark", action="store_true", help="Execute search benchmark evaluation")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show full rules, anti-patterns, and BM25 explanations")

    args = parser.parse_args()

    if args.validate:
        success, messages = validate_knowledge_base(force_fallback=args.fallback)
        if args.json:
            print(json.dumps({"valid": success, "messages": messages}, indent=2))
        else:
            if success:
                print(f"[OK] {messages[0]}")
            else:
                print(f"[ERROR] Schema validation failed with {len(messages)} error(s):")
                for m in messages:
                    print(f"  • {m}")
        sys.exit(0 if success else 1)

    if args.benchmark:
        try:
            metrics = run_search_benchmark()
            if args.json:
                print(json.dumps(metrics, indent=2, ensure_ascii=False))
            else:
                print("╔═════════════════════════════════════════════════════════════════════════════╗")
                print("║               ORTHOTECT KNOWLEDGE SEARCH QUALITY BENCHMARK                  ║")
                print("╚═════════════════════════════════════════════════════════════════════════════╝\n")
                print(f"Total Benchmark Queries : {metrics['total_queries']}")
                print(f"Mean Reciprocal Rank    : {metrics['mrr']} (Threshold >= 0.75)")
                print(f"Precision@1             : {metrics['precision_at_1']} (Threshold >= 0.70)")
                print(f"Precision@3             : {metrics['precision_at_3']}")
                print(f"Recall@3                : {metrics['recall_at_3']} (Threshold >= 0.65)")
                print(f"Recall@5                : {metrics['recall_at_5']}\n")
                
                passed = metrics['mrr'] >= 0.75 and metrics['precision_at_1'] >= 0.70 and metrics['recall_at_3'] >= 0.65
                status_str = "✅ [BENCHMARK PASSED] Search quality meets enterprise thresholds." if passed else "❌ [BENCHMARK FAILED] Below threshold."
                print(status_str)
                sys.exit(0 if passed else 1)

        except Exception as e:
            print(f"[ERROR] Benchmark execution failed: {e}")
            sys.exit(1)

    results = search_knowledge(
        query=args.query,
        category=args.category,
        tag=args.tag,
        stack=args.stack,
        limit=args.limit
    )

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
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
        status_symbol = f"[{res['verificationStatus']}]"
        print(f"{i}. {res['title']} ({res['category']}) {status_symbol} [BM25: {res['score']}]")
        print(f"   ID: {res['id']} | Source: {res['source']}")
        print(f"   Summary: {res['summary']}")
        print(f"   Tags: {', '.join(res['tags'][:6])}")
        
        if args.verbose:
            if res.get("_score_explanation"):
                print("   BM25 Term Explanation:")
                for term, exp in res["_score_explanation"].items():
                    print(f"     • {term}: tf={exp['tf']}, idf={exp['idf']}, contrib={exp['contrib']}")
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
