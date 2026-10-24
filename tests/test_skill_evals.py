import unittest
import os
import json

class TestSkillEvals(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.skills_dir = os.path.join(self.root_dir, 'skills')

    def test_eval_files_schema_and_assertions(self):
        """Validate that all skill evaluation fixtures adhere strictly to the schema."""
        eval_files_found = 0
        for root, dirs, files in os.walk(self.skills_dir):
            if 'evals.json' in files:
                eval_files_found += 1
                filepath = os.path.join(root, 'evals.json')
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.assertIn("skill_name", data, f"Missing skill_name in {filepath}")
                self.assertIn("evals", data, f"Missing evals array in {filepath}")
                self.assertIsInstance(data["evals"], list)
                self.assertGreater(len(data["evals"]), 0, f"Empty evals list in {filepath}")

                has_positive = False
                has_negative = False

                for item in data["evals"]:
                    self.assertIn("id", item)
                    self.assertIsInstance(item["id"], int)
                    self.assertIn("prompt", item)
                    self.assertIsInstance(item["prompt"], str)
                    self.assertGreater(len(item["prompt"].strip()), 5)

                    self.assertIn("expected_output", item)
                    self.assertIsInstance(item["expected_output"], str)
                    self.assertGreater(len(item["expected_output"].strip()), 5)

                    self.assertIn("assertions", item)
                    self.assertIsInstance(item["assertions"], list)
                    self.assertGreater(len(item["assertions"]), 0)

                    if item.get("negative", False):
                        has_negative = True
                    else:
                        has_positive = True

                self.assertTrue(has_positive, f"Eval suite in {filepath} must contain at least one positive test")
                self.assertTrue(has_negative, f"Eval suite in {filepath} must contain at least one negative trigger test")

        self.assertGreaterEqual(eval_files_found, 2, "Expected at least 2 skill eval suites")

    def test_schema_jsonld_reference_templates_validity(self):
        """Validate that all JSON-LD code templates in skills/orthotect-schema/ parse as valid Schema.org JSON."""
        templates_md = os.path.join(self.skills_dir, 'orthotect-schema', 'references', 'jsonld-templates.md')
        self.assertTrue(os.path.isfile(templates_md), f"Missing {templates_md}")

        with open(templates_md, 'r', encoding='utf-8') as f:
            content = f.read()

        import re
        # Extract jsonld script blocks
        json_blocks = re.findall(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', content, re.DOTALL)
        self.assertGreaterEqual(len(json_blocks), 3, "Expected at least 3 JSON-LD template snippets")

        for idx, block in enumerate(json_blocks):
            try:
                data = json.loads(block)
            except Exception as e:
                self.fail(f"JSON-LD template #{idx+1} in {templates_md} is invalid JSON: {e}")

            self.assertEqual(data.get("@context"), "https://schema.org", f"Template #{idx+1} must define @context 'https://schema.org'")
            has_type_or_graph = "@type" in data or "@graph" in data
            self.assertTrue(has_type_or_graph, f"Template #{idx+1} must contain @type or @graph")

            # Verify that replacing template placeholders results in valid production JSON
            rendered = (
                block.replace("{{APP_NAME}}", "MyProduct")
                .replace("{{WEBSITE_URL}}", "https://myproduct.example.com")
                .replace("{{PRICE}}", "29.99")
                .replace("{{SUPPORT_URL}}", "https://myproduct.example.com/support")
            )
            parsed_rendered = json.loads(rendered)
            self.assertIsNotNone(parsed_rendered)

            if "@graph" in data:
                # First template is the unified SaaS homepage @graph
                app_entities = [e for e in data["@graph"] if e.get("@type") == "SoftwareApplication"]
                self.assertEqual(len(app_entities), 1)
                app = app_entities[0]
                self.assertIn("name", app, "SoftwareApplication template must include name")
                self.assertIn("offers", app, "SoftwareApplication template must include offers")
                self.assertEqual(app["offers"].get("price"), "{{PRICE}}")
                # Ensure templates do not hardcode fake review scores or counts
                self.assertNotIn("120", str(block), "Templates must not hardcode fabricated review counts")

if __name__ == '__main__':
    unittest.main()
