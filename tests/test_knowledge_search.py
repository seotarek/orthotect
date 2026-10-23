import unittest
import os
import sys
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.knowledge_search import (
    load_knowledge_base,
    search_knowledge,
    validate_knowledge_base,
    calculate_relevance,
    tokenize
)

class TestKnowledgeSearch(unittest.TestCase):
    def setUp(self):
        self.root_dir = ROOT_DIR
        self.knowledge_dir = os.path.join(self.root_dir, 'knowledge')
        self.schemas_dir = os.path.join(self.knowledge_dir, 'schemas')

    def test_load_knowledge_base_discovers_all_records(self):
        """Verify load_knowledge_base discovers all style recipes and knowledge records."""
        records = load_knowledge_base(self.knowledge_dir)
        self.assertGreaterEqual(len(records), 16, "Must discover at least 16 records & recipes")
        
        # Check presence of style recipes
        recipes = [r for r in records if r.get("_type") == "style-recipe"]
        self.assertGreaterEqual(len(recipes), 6, "Must load at least 6 style recipes")
        
        recipe_ids = [r["id"] for r in recipes]
        self.assertIn("restrained-editorial-clarity", recipe_ids)
        self.assertIn("precision-analytical-console", recipe_ids)
        self.assertIn("contemporary-product-saas", recipe_ids)
        self.assertIn("high-density-operational", recipe_ids)
        self.assertIn("material-led-commerce", recipe_ids)
        self.assertIn("accessible-high-contrast", recipe_ids)

    def test_validate_knowledge_base_against_schemas(self):
        """Verify that every record in the knowledge base strictly passes JSON schema validation."""
        valid, messages = validate_knowledge_base(self.knowledge_dir, self.schemas_dir)
        self.assertTrue(valid, f"Knowledge base schema validation failed: {messages}")
        self.assertTrue(any("Successfully validated" in m for m in messages))

    def test_search_by_query_keyword(self):
        """Verify search_knowledge correctly finds records matching keyword query."""
        results = search_knowledge(query="contrast", knowledge_dir=self.knowledge_dir)
        self.assertGreater(len(results), 0, "Query 'contrast' must return results")
        
        top_ids = [r["id"] for r in results]
        self.assertTrue(
            "semantic-roles" in top_ids or "wcag-matrix" in top_ids or "accessible-high-contrast" in top_ids,
            "Top results for 'contrast' must include core contrast records"
        )

    def test_search_filter_by_category(self):
        """Verify category filtering isolates only records in that category."""
        styles_results = search_knowledge(category="styles", knowledge_dir=self.knowledge_dir)
        self.assertEqual(len(styles_results), 6)
        for r in styles_results:
            self.assertEqual(r["category"], "styles")

        bidi_results = search_knowledge(category="bidi", knowledge_dir=self.knowledge_dir)
        self.assertGreaterEqual(len(bidi_results), 1)
        for r in bidi_results:
            self.assertEqual(r["category"], "bidi")

    def test_search_filter_by_tag(self):
        """Verify tag filtering matches records containing the specified tag."""
        bidi_tagged = search_knowledge(tag="bidi", knowledge_dir=self.knowledge_dir)
        self.assertGreater(len(bidi_tagged), 0)
        for r in bidi_tagged:
            tags_lower = [t.lower() for t in r["tags"]]
            self.assertIn("bidi", tags_lower)

    def test_search_filter_by_stack(self):
        """Verify stack filtering returns records compatible with target stack."""
        react_records = search_knowledge(stack="react", knowledge_dir=self.knowledge_dir)
        self.assertGreater(len(react_records), 0)
        for r in react_records:
            stacks = [s.lower() for s in r["applicableStacks"]]
            self.assertTrue("react" in stacks or "universal" in stacks)

    def test_relevance_ranking_prioritizes_title_matches(self):
        """Verify that a title match receives higher relevance than a body match."""
        # Query that appears in title of 'logical-rules'
        title_record = {
            "title": "Bidirectional Logical Properties",
            "id": "bidi-title",
            "tags": [],
            "summary": "overview",
            "rules": []
        }
        body_record = {
            "title": "Other Topic",
            "id": "other",
            "tags": [],
            "summary": "mentions bidirectional in passing",
            "rules": []
        }
        tokens = tokenize("bidirectional")
        score_title = calculate_relevance(title_record, tokens)
        score_body = calculate_relevance(body_record, tokens)
        self.assertGreater(score_title, score_body, "Title match must outscore body match")

    def test_record_structure_contains_provenance_and_verification_status(self):
        """Verify all search results return provenance and standardized verification status."""
        results = search_knowledge(limit=20, knowledge_dir=self.knowledge_dir)
        for r in results:
            self.assertIn("provenance", r)
            self.assertIn("verificationStatus", r)
            self.assertIn(r["verificationStatus"], ["VERIFIED_DETERMINISTIC", "VERIFIED_BROWSER", "HEURISTIC", "NOT_EVALUATED"])
            self.assertIn("source", r)

    # -------------------------------------------------------------
    # Area 1: Negative Schema Validation Tests
    # -------------------------------------------------------------
    def test_schema_rejects_missing_required_property(self):
        """Negative test: Missing required fields must be detected and rejected."""
        from core.knowledge_search import _validate_schema_builtin
        schema = {
            "type": "object",
            "required": ["id", "title"],
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"}
            }
        }
        errs = _validate_schema_builtin({"id": "only-id"}, schema)
        self.assertTrue(any("Missing required property: 'title'" in e for e in errs))

    def test_schema_rejects_boolean_in_numeric_field(self):
        """Negative test: Python bool must NOT satisfy integer or number type constraints."""
        from core.knowledge_search import _validate_schema_builtin
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "ratio": {"type": "number"}
            }
        }
        # True is a subclass of int in Python, but JSON Schema rejects boolean for integer/number
        errs_int = _validate_schema_builtin({"count": True}, schema)
        self.assertTrue(any("Property 'count' must be an integer, got bool" in e for e in errs_int))

        errs_num = _validate_schema_builtin({"ratio": False}, schema)
        self.assertTrue(any("Property 'ratio' must be a number, got bool" in e for e in errs_num))

    def test_schema_rejects_incorrect_nested_types(self):
        """Negative test: Nested objects and array item type violations must be recursively reported."""
        from core.knowledge_search import _validate_schema_builtin
        schema = {
            "type": "object",
            "properties": {
                "evidence": {
                    "type": "object",
                    "properties": {
                        "humanReviewed": {"type": "boolean"},
                        "gatesPassed": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        }
        bad_data = {
            "evidence": {
                "humanReviewed": "not-a-bool",
                "gatesPassed": ["gate1", 12345]  # number inside string array
            }
        }
        errs = _validate_schema_builtin(bad_data, schema)
        self.assertTrue(any("humanReviewed' must be a boolean" in e for e in errs))
        self.assertTrue(any("gatesPassed[1]: Expected string, got int" in e for e in errs))

    def test_schema_rejects_invalid_nested_enums(self):
        """Negative test: Invalid enum values must be detected and rejected."""
        from core.knowledge_search import _validate_schema_builtin
        schema = {
            "type": "object",
            "properties": {
                "verificationStatus": {
                    "type": "string",
                    "enum": ["NOT_EVALUATED", "HEURISTIC", "VERIFIED_DETERMINISTIC", "VERIFIED_BROWSER"]
                }
            }
        }
        errs = _validate_schema_builtin({"verificationStatus": "FAKE_STATUS"}, schema)
        self.assertTrue(any("not in allowed enum" in e for e in errs))

    def test_schema_fails_closed_on_unsupported_keywords_in_strict_mode(self):
        """Negative test: Strict fallback mode fails closed on unsupported schema constraints."""
        from core.knowledge_search import _validate_schema_builtin
        schema = {
            "type": "object",
            "unsupportedKeyword123": True,
            "properties": {"id": {"type": "string"}}
        }
        errs = _validate_schema_builtin({"id": "test"}, schema, strict_mode=True)
        self.assertTrue(any("Unsupported schema keyword(s)" in e and "unsupportedKeyword123" in e for e in errs))




    def test_forced_fallback_mode_matches_jsonschema(self):
        """Consistency test: validate_knowledge_base with force_fallback=True must successfully validate the real knowledge base."""
        valid_full, msg_full = validate_knowledge_base(self.knowledge_dir, self.schemas_dir, force_fallback=False)
        valid_fb, msg_fb = validate_knowledge_base(self.knowledge_dir, self.schemas_dir, force_fallback=True)
        self.assertTrue(valid_full)
        self.assertTrue(valid_fb)

    # -------------------------------------------------------------
    # Area 4: BM25 Search Quality and Arabic Tokenization Tests
    # -------------------------------------------------------------
    def test_arabic_unicode_tokenization_and_normalization(self):
        """Arabic queries must be normalized (alef variants, teh marbuta) and tokenized accurately."""
        from core.knowledge_search import normalize_text, tokenize
        raw_ar = "تَبايُنُ الألوانِ المُتَناسِقَة"
        norm = normalize_text(raw_ar)
        tokens = tokenize(raw_ar)
        self.assertIn("تباين", tokens)
        self.assertIn("الالوان", tokens)

    def test_search_benchmark_metrics_meet_acceptance_thresholds(self):
        """Benchmark verification: Search quality over benchmark queries must satisfy enterprise thresholds."""
        from core.knowledge_search import run_search_benchmark
        metrics = run_search_benchmark()
        self.assertEqual(metrics["total_queries"], 32, f"Total benchmark queries must be 32, got {metrics['total_queries']}")
        self.assertGreaterEqual(metrics["mrr"], 0.75, f"MRR {metrics['mrr']} must meet >= 0.75 threshold")
        self.assertGreaterEqual(metrics["precision_at_1"], 0.70, f"P@1 {metrics['precision_at_1']} must meet >= 0.70 threshold")
        self.assertGreaterEqual(metrics["recall_at_3"], 0.65, f"Recall@3 {metrics['recall_at_3']} must meet >= 0.65 threshold")

    def test_search_benchmark_dataset_contains_32_queries(self):
        """Verify the expanded benchmark dataset contains all 32 diverse queries."""
        from core.knowledge_search import DEFAULT_BENCHMARK_PATH
        with open(DEFAULT_BENCHMARK_PATH, 'r', encoding='utf-8') as f:
            benchmarks = json.load(f)
        self.assertEqual(len(benchmarks), 32)
        arabic_queries = [b for b in benchmarks if b.get('intent', '').startswith('arabic-')]
        self.assertGreaterEqual(len(arabic_queries), 6)

    def test_no_result_query_returns_empty_list(self):
        """Search query with nonsense tokens must return clean empty list without exceptions."""
        results = search_knowledge(query="xyznonexistenttoken9999", knowledge_dir=self.knowledge_dir)
        self.assertEqual(len(results), 0)

    # -------------------------------------------------------------
    # Area 5: Evidence-Based Verification Status Derivation Tests
    # -------------------------------------------------------------
    def test_status_derivation_without_evidence_is_not_evaluated(self):
        """Schema-valid item with no evidence must derive NOT_EVALUATED, never a false verification claim."""
        from core.knowledge_search import derive_verification_status
        record_no_evidence = { "id": "test", "title": "Untested Recipe" }
        status = derive_verification_status(record_no_evidence)
        self.assertEqual(status, "NOT_EVALUATED")

    def test_status_derivation_with_gates_is_verified_deterministic(self):
        """Record with automated gatesPassed evidence and provenance derives VERIFIED_DETERMINISTIC."""
        from core.knowledge_search import derive_verification_status
        record_gate_evidence = {
            "id": "test",
            "evidence": {
                "gatesPassed": ["gate_contrast_wcag.py", "gate_bidi_logical.py"],
                "verifier": "orthotect-gate-runner",
                "verifiedAt": "2026-10-23T07:00:00Z",
                "revision": "68399b3"
            }
        }
        status = derive_verification_status(record_gate_evidence)
        self.assertEqual(status, "VERIFIED_DETERMINISTIC")

    def test_status_derivation_rejects_unverified_gate_claims(self):
        """Negative test: Claiming gatesPassed without verifier/timestamp/revision must fall back to NOT_EVALUATED."""
        from core.knowledge_search import derive_verification_status
        fake_gate_record = {
            "id": "test",
            "evidence": {
                "gatesPassed": ["gate_contrast_wcag.py"]  # Missing verifier, verifiedAt, revision!
            }
        }
        self.assertEqual(derive_verification_status(fake_gate_record), "NOT_EVALUATED")

        unrecognized_gate_record = {
            "id": "test",
            "evidence": {
                "gatesPassed": ["fake_nonexistent_gate.py"],
                "verifier": "test",
                "verifiedAt": "2026-10-23T07:00:00Z",
                "revision": "v1.6.0"
            }
        }
        self.assertEqual(derive_verification_status(unrecognized_gate_record), "NOT_EVALUATED")

    def test_status_derivation_with_browser_is_verified_browser(self):
        """Record with browser verified DOM evidence and provenance derives VERIFIED_BROWSER."""
        from core.knowledge_search import derive_verification_status
        record_browser_evidence = {
            "id": "test",
            "evidence": {
                "browserVerified": True,
                "browserEvidence": {
                    "testSuite": "tests/verify_browser_contrast.mjs",
                    "testedThemes": ["light", "dark"],
                    "verifiedAt": "2026-10-23T07:00:00Z"
                },
                "verifier": "playwright-browser-runner",
                "verifiedAt": "2026-10-23T07:00:00Z",
                "revision": "68399b3"
            }
        }
        status = derive_verification_status(record_browser_evidence)
        self.assertEqual(status, "VERIFIED_BROWSER")

    def test_status_derivation_rejects_unverified_browser_claims(self):
        """Negative test: Claiming browserVerified without browserEvidence details must fall back to NOT_EVALUATED."""
        from core.knowledge_search import derive_verification_status
        unproven_browser = {
            "id": "test",
            "evidence": {
                "browserVerified": True  # Missing browserEvidence, verifier, etc.
            }
        }
        self.assertEqual(derive_verification_status(unproven_browser), "NOT_EVALUATED")

    def test_status_derivation_with_heuristic_advice(self):
        """Advisory/opinion design principles without deterministic gates derive HEURISTIC."""
        from core.knowledge_search import derive_verification_status
        record_heuristic = {
            "id": "test",
            "evidence": {
                "heuristic": True
            }
        }
        status = derive_verification_status(record_heuristic)
        self.assertEqual(status, "HEURISTIC")

    def test_builtin_validator_enforces_pattern_and_string_lengths(self):
        """Builtin validator rejects strings that violate pattern or length constraints."""
        from core.knowledge_search import _validate_schema_builtin
        schema = {
            "type": "object",
            "properties": {
                "slug": { "type": "string", "pattern": "^[a-z0-9-]+$", "minLength": 3, "maxLength": 10 }
            }
        }
        # Valid
        self.assertEqual(_validate_schema_builtin({"slug": "test-slug"}, schema), [])
        # Invalid pattern (uppercase or spaces)
        errs = _validate_schema_builtin({"slug": "INVALID SLUG"}, schema)
        self.assertTrue(any("does not match pattern" in e for e in errs))
        # Invalid length (too short)
        errs_short = _validate_schema_builtin({"slug": "ab"}, schema)
        self.assertTrue(any("too short" in e for e in errs_short))
        # Invalid length (too long)
        errs_long = _validate_schema_builtin({"slug": "a-very-long-slug"}, schema)
        self.assertTrue(any("too long" in e for e in errs_long))

    def test_builtin_validator_enforces_additional_properties_false(self):
        """Builtin validator rejects extraneous properties when additionalProperties is False."""
        from core.knowledge_search import _validate_schema_builtin
        schema = {
            "type": "object",
            "properties": {
                "name": { "type": "string" }
            },
            "additionalProperties": False
        }
        valid_res = _validate_schema_builtin({"name": "valid"}, schema)
        self.assertEqual(valid_res, [])
        invalid_res = _validate_schema_builtin({"name": "valid", "extra_prop": 123}, schema)
        self.assertTrue(any("Additional property 'extra_prop' is not allowed" in e for e in invalid_res))

    def test_builtin_validator_rejects_unsupported_keywords_in_leaf_property_schemas(self):
        """Builtin validator rejects unsupported keywords even inside simple leaf property schemas."""
        from core.knowledge_search import _validate_schema_builtin
        schema_with_leaf_unknown = {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "unsupportedKeywordX": "not_supported"
                }
            }
        }
        errs = _validate_schema_builtin({"title": "Test Title"}, schema_with_leaf_unknown, strict_mode=True)
        self.assertTrue(any("Unsupported schema keyword(s)" in e for e in errs))

    def test_builtin_validator_rejects_unsupported_keywords_in_array_items_schema(self):
        """Builtin validator rejects unsupported keywords inside array items schemas."""
        from core.knowledge_search import _validate_schema_builtin
        schema_with_items_unknown = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "unsupportedKeywordY": "bad"
                    }
                }
            }
        }
        errs = _validate_schema_builtin({"tags": ["sample"]}, schema_with_items_unknown, strict_mode=True)
        self.assertTrue(any("Unsupported schema keyword(s)" in e for e in errs))

    def test_builtin_validator_validates_root_array_items(self):
        """Builtin validator correctly validates root array items and rejects item type mismatches."""
        from core.knowledge_search import _validate_schema_builtin
        array_schema = {
            "type": "array",
            "items": { "type": "string" }
        }
        valid_res = _validate_schema_builtin(["a", "b", "c"], array_schema)
        self.assertEqual(valid_res, [])
        invalid_res = _validate_schema_builtin(["a", 123, "c"], array_schema)
        self.assertTrue(any("Expected string" in e for e in invalid_res))

    def test_builtin_validator_enforces_root_string_and_numeric_constraints(self):
        """Builtin validator enforces pattern, minLength, maxLength, minimum, maximum, and enum at root level."""
        from core.knowledge_search import _validate_schema_builtin
        str_schema = {
            "type": "string",
            "minLength": 3,
            "maxLength": 8,
            "pattern": r"^[a-z]+$"
        }
        self.assertEqual(_validate_schema_builtin("valid", str_schema), [])
        err_short = _validate_schema_builtin("ab", str_schema)
        self.assertTrue(any("too short" in e for e in err_short))
        err_long = _validate_schema_builtin("toolongstring", str_schema)
        self.assertTrue(any("too long" in e for e in err_long))
        err_pattern = _validate_schema_builtin("12345", str_schema)
        self.assertTrue(any("does not match pattern" in e for e in err_pattern))

        num_schema = {
            "type": "integer",
            "minimum": 10,
            "maximum": 50,
            "enum": [10, 20, 30, 40, 50]
        }
        self.assertEqual(_validate_schema_builtin(20, num_schema), [])
        err_min = _validate_schema_builtin(5, num_schema)
        self.assertTrue(any("minimum" in e for e in err_min))
        err_max = _validate_schema_builtin(60, num_schema)
        self.assertTrue(any("maximum" in e for e in err_max))
        err_enum = _validate_schema_builtin(25, num_schema)
        self.assertTrue(any("not in allowed enum" in e for e in err_enum))

if __name__ == '__main__':
    unittest.main()


