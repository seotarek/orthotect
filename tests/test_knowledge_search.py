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
            self.assertIn(r["verificationStatus"], ["VERIFIED_DETERMINISTIC", "VERIFIED_BROWSER", "HEURISTIC"])
            self.assertIn("source", r)

if __name__ == '__main__':
    unittest.main()
