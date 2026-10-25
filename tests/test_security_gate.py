#!/usr/bin/env python3
"""
Unit tests for Orthotect Deterministic Quality Gate 6: Enterprise Security & Vulnerability Audit.
Verifies exploit detection across OWASP Top 10, CWE Top 25, and ensures zero false positives on clean code.
"""

import unittest
import tempfile
import os
import shutil
from gates.gate_security_audit import scan_file, main

class TestSecurityAuditGate(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="ortho_sec_test_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _create_temp_file(self, filename, content):
        path = os.path.join(self.temp_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    # 1. SQL Injection Tests
    def test_sql_injection_python_fstring(self):
        content = """
def get_user(cursor, user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
"""
        fpath = self._create_temp_file("sqli_fstring.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("SQL Injection" in f[1] for f in findings))

    def test_sql_injection_python_concat(self):
        content = """
def get_user(cursor, username):
    cursor.execute("SELECT * FROM users WHERE username = '" + username + "'")
"""
        fpath = self._create_temp_file("sqli_concat.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("SQL Injection" in f[1] for f in findings))

    def test_sql_injection_safe_parameterized(self):
        content = """
def get_user(cursor, user_id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
"""
        fpath = self._create_temp_file("sqli_safe.py", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    # 2. Command Injection Tests
    def test_command_injection_nodejs(self):
        content = """
const cp = require('child_process');
function runGit(repo) {
    cp.exec(`git clone ${repo}`);
}
"""
        fpath = self._create_temp_file("cmd_node.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("OS Command Injection" in f[1] for f in findings))

    def test_command_injection_subprocess_shell_true(self):
        content = """
import subprocess
def ping_host(host):
    subprocess.Popen(f"ping -c 1 {host}", shell=True)
"""
        fpath = self._create_temp_file("cmd_py.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("subprocess invocation with shell=True" in f[1] for f in findings))

    def test_command_safe_exec_array(self):
        content = """
import subprocess
def ping_host(host):
    subprocess.run(["ping", "-c", "1", host], shell=False)
"""
        fpath = self._create_temp_file("cmd_safe.py", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    # 3. DOM XSS Tests
    def test_dom_xss_location_sink(self):
        content = """
function renderNotice() {
    const box = document.getElementById("notice");
    box.innerHTML = location.search;
}
"""
        fpath = self._create_temp_file("dom_xss.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("DOM XSS" in f[1] for f in findings))

    def test_dom_xss_safe_sanitized(self):
        content = """
function renderNotice() {
    const box = document.getElementById("notice");
    box.textContent = "Safe notification message";
}
"""
        fpath = self._create_temp_file("dom_xss_safe.js", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    # 4. SSRF Tests
    def test_ssrf_internal_ip(self):
        content = """
async function fetchMetadata() {
    const res = await fetch("http://169.254.169.254/latest/meta-data/");
    return res.text();
}
"""
        fpath = self._create_temp_file("ssrf.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Server-Side Request Forgery" in f[1] for f in findings))

    def test_ssrf_localhost(self):
        content = """
import requests
def call_internal():
    return requests.get("http://127.0.0.1:8080/admin")
"""
        fpath = self._create_temp_file("ssrf_py.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Server-Side Request Forgery" in f[1] for f in findings))

    # 5. Path Traversal Tests
    def test_path_traversal(self):
        content = """
const fs = require('fs');
function loadConfig(name) {
    return fs.readFileSync('../config/' + name);
}
"""
        fpath = self._create_temp_file("traversal.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Path Traversal" in f[1] for f in findings))

    # 6. Hardcoded Secrets Tests
    def test_hardcoded_aws_key(self):
        content = """
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
"""
        fpath = self._create_temp_file("aws_leak.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("AWS Access Key" in f[1] for f in findings))

    def test_hardcoded_production_key(self):
        content = """
API_KEY = "live_secret_key_849204820482048204820"
"""
        fpath = self._create_temp_file("prod_leak.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Production Secret Key" in f[1] for f in findings))

    def test_hardcoded_github_pat(self):
        content = """
GH_TOKEN = "ghp_123456789012345678901234567890123456"
"""
        fpath = self._create_temp_file("gh_leak.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("GitHub Personal Access Token" in f[1] for f in findings))

    # 7. Insecure Deserialization Tests
    def test_insecure_pickle(self):
        content = """
import pickle
def unpack(data):
    return pickle.loads(data)
"""
        fpath = self._create_temp_file("pickle_vuln.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Insecure Deserialization" in f[1] for f in findings))

    # 8. Prototype Pollution Tests
    def test_prototype_pollution(self):
        content = """
function merge(target, source) {
    target.__proto__ = source;
}
"""
        fpath = self._create_temp_file("proto.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Prototype Pollution" in f[1] for f in findings))

    # 9. Insecure PostMessage Tests
    def test_insecure_postmessage(self):
        content = """
function broadcastToken(token) {
    window.postMessage({ token }, "*");
}
"""
        fpath = self._create_temp_file("postmsg.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Insecure Cross-Origin postMessage" in f[1] for f in findings))

    # 10. False Positive Prevention Tests
    def test_false_positive_static_relative_read(self):
        content = """
import fs from 'fs';
const data = fs.readFileSync(new URL('../package.json', import.meta.url), 'utf8');
"""
        fpath = self._create_temp_file("static_read.mjs", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    def test_false_positive_python_tuple_and_list_insert(self):
        content = """
import sys
keywords = ('delete', 'void', 'throw', 'yield', 'await', 'default')
sys.path.insert(0, '/root')
"""
        fpath = self._create_temp_file("tuple_insert.py", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    # 11. Environment File (.env) Scanning Tests
    def test_env_files_detected_in_directory_scan(self):
        env_path = self._create_temp_file(".env", 'SECRET_KEY = "prod_secret_849204820482048204820"\n')
        env_local_path = self._create_temp_file(".env.local", 'AUTH_TOKEN = "production_key_99999999999999999999"\n')
        env_prod_path = self._create_temp_file(".env.production", 'API_KEY = "test_secret_key_abcdef1234567890123456"\n')

        # Test scan_file directly
        self.assertTrue(len(scan_file(env_path)) > 0)
        self.assertTrue(len(scan_file(env_local_path)) > 0)
        self.assertTrue(len(scan_file(env_prod_path)) > 0)

        # Test directory discovery logic
        from gates.gate_security_audit import is_scannable_file
        self.assertTrue(is_scannable_file(".env"))
        self.assertTrue(is_scannable_file(".env.local"))
        self.assertTrue(is_scannable_file(".env.production"))

    # 12. YAML Deserialization Tests (Safe vs Unsafe)
    def test_yaml_safe_loader_not_flagged(self):
        content = """
import yaml
def load_config(text):
    return yaml.load(text, Loader=yaml.SafeLoader)
"""
        fpath = self._create_temp_file("yaml_safe.py", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    def test_yaml_safe_loader_direct_import_not_flagged(self):
        content = """
from yaml import load, SafeLoader
def load_config(text):
    return load(text, Loader=SafeLoader)
"""
        fpath = self._create_temp_file("yaml_safe_direct.py", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    def test_yaml_unsafe_load_flagged(self):
        content = """
import yaml
def load_config(text):
    return yaml.unsafe_load(text)
"""
        fpath = self._create_temp_file("yaml_unsafe.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("yaml.unsafe_load" in f[1] for f in findings))

    def test_yaml_load_no_loader_flagged(self):
        content = """
import yaml
def load_config(text):
    return yaml.load(text)
"""
        fpath = self._create_temp_file("yaml_no_loader.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("without SafeLoader" in f[1] for f in findings))

    def test_yaml_load_unsafe_loader_flagged(self):
        content = """
import yaml
def load_config(text):
    return yaml.load(text, Loader=yaml.Loader)
"""
        fpath = self._create_temp_file("yaml_unsafe_loader.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("without SafeLoader" in f[1] for f in findings))

    def test_yaml_direct_import_unsafe_load_flagged(self):
        content = """
from yaml import unsafe_load
def load_config(text):
    return unsafe_load(text)
"""
        fpath = self._create_temp_file("yaml_unsafe_direct.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("yaml.unsafe_load" in f[1] for f in findings))

    def test_yaml_alias_unsafe_load_flagged(self):
        content = """
import yaml as y
def load_config(text):
    return y.unsafe_load(text)
"""
        fpath = self._create_temp_file("yaml_unsafe_alias.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("yaml.unsafe_load" in f[1] for f in findings))

    def test_yaml_direct_import_load_no_loader_flagged(self):
        content = """
from yaml import load
def load_config(text):
    return load(text)
"""
        fpath = self._create_temp_file("yaml_direct_no_loader.py", content)
        findings = scan_file(fpath)
        self.assertTrue(any("without SafeLoader" in f[1] for f in findings))

    def test_yaml_alias_safe_loader_not_flagged(self):
        content = """
import yaml as y
def load_config(text):
    return y.load(text, Loader=y.SafeLoader)
"""
        fpath = self._create_temp_file("yaml_alias_safe.py", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    # 13. Intra-file Taint Tracking Tests
    def test_indirect_dom_xss_taint_propagation(self):
        content = """
function displayUserMessage() {
    const rawInput = location.search;
    const msg = rawInput;
    document.getElementById("output").innerHTML = msg;
}
"""
        fpath = self._create_temp_file("taint_xss.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Taint Flow" in f[1] for f in findings))

    def test_indirect_dom_xss_sanitized_flow(self):
        content = """
function displayUserMessage() {
    const rawInput = DOMPurify.sanitize(location.search);
    document.getElementById("output").innerHTML = rawInput;
}
"""
        fpath = self._create_temp_file("taint_safe.js", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    def test_indirect_dom_xss_method_chain_taint(self):
        content = """
function displayUserMessage() {
    const rawInput = location.search;
    const msg = rawInput.trim().toLowerCase();
    document.getElementById("output").innerHTML = msg;
}
"""
        fpath = self._create_temp_file("taint_chain.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Taint Flow" in f[1] for f in findings))

    def test_indirect_dom_xss_direct_method_chain_to_sink(self):
        content = """
function displayUserMessage() {
    const rawInput = location.search;
    document.getElementById("output").innerHTML = rawInput.trim();
}
"""
        fpath = self._create_temp_file("taint_direct_chain.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Taint Flow" in f[1] for f in findings))

    def test_indirect_dom_xss_concat_taint(self):
        content = """
function displayUserMessage() {
    const rawInput = location.search;
    const msg = "<b>Message:</b> " + rawInput;
    document.getElementById("output").innerHTML = msg;
}
"""
        fpath = self._create_temp_file("taint_concat.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Taint Flow" in f[1] for f in findings))

    def test_indirect_dom_xss_sanitized_in_chain(self):
        content = """
function displayUserMessage() {
    const rawInput = location.search;
    const msg = DOMPurify.sanitize(rawInput).trim();
    document.getElementById("output").innerHTML = msg;
}
"""
        fpath = self._create_temp_file("taint_sanitized_chain.js", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    def test_indirect_dom_xss_mixed_expression_assignment_flagged(self):
        content = """
function displayUserMessage() {
    const raw = location.search;
    const mixed = DOMPurify.sanitize(raw) + raw;
    document.getElementById("output").innerHTML = mixed;
}
"""
        fpath = self._create_temp_file("taint_mixed.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Taint Flow" in f[1] for f in findings))

    def test_indirect_dom_xss_direct_mixed_sink_flagged(self):
        content = """
function displayUserMessage() {
    const raw = location.search;
    document.getElementById("output").innerHTML = DOMPurify.sanitize(raw) + raw;
}
"""
        fpath = self._create_temp_file("taint_direct_mixed.js", content)
        findings = scan_file(fpath)
        self.assertTrue(any("Taint Flow" in f[1] for f in findings))

    def test_indirect_dom_xss_reassignment_to_sanitized_clears_taint(self):
        content = """
function displayUserMessage() {
    let msg = location.search;
    msg = DOMPurify.sanitize(msg);
    document.getElementById("output").innerHTML = msg;
}
"""
        fpath = self._create_temp_file("taint_reassign_sanitized.js", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

    def test_indirect_dom_xss_reassignment_to_safe_static_clears_taint(self):
        content = """
function displayUserMessage() {
    let raw = location.search;
    raw = "Safe static system notification";
    document.getElementById("output").innerHTML = raw;
}
"""
        fpath = self._create_temp_file("taint_reassign_static.js", content)
        findings = scan_file(fpath)
        self.assertEqual(len(findings), 0)

if __name__ == '__main__':
    unittest.main()
