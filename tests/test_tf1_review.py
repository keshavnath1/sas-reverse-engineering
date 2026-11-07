"""Two approved fixtures through the existing offline developer entry point."""

from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
import uuid

from p2a_expectations import PUBLIC_CASES
from test_review_workflow import ROOT, PREVIEWS, STATUS, OFFLINE, call, free_destination, remove_destination

STATE_GRAPH = '6ec1a62ae2180e05c54c69f6f15a02ecd4678ee925fb37f29796ba7d2842c965'
SOURCE_HASH = '6137125dd383492459116ea7a507ed8f0100219c2b66681c38ee5b6719055c49'
EXPECTATIONS_HASH = 'f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93'


@unittest.skipUnless(sys.platform in ('darwin', 'linux'), 'Synthetic fixture I/O requires POSIX')
class TwoFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dest = Path('/tmp') / ('review-tf1-' + uuid.uuid4().hex)
        cls.addClassCleanup(remove_destination, cls.dest)
        run = call(cls.dest, extra=('--fixture', 'by-retain-and-sum'), guard=OFFLINE)
        if run.returncode:
            raise AssertionError(run.stderr.decode())
        cls.command_result = run
        cls.files = {p.name: p.read_bytes() for p in cls.dest.iterdir()}
        cls.manifest = json.loads(cls.files['MANIFEST.json'])

    def test_closed_selection_and_legacy_explicit_mvp2(self):
        for argv in (('--fixture', 'unknown'), ('--fixture', '../main.sas'),
                     ('--fixture', 'mvp2', '--fixture', 'by-retain-and-sum')):
            dest = free_destination()
            self.addCleanup(remove_destination, dest)
            result = call(dest, extra=argv)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(dest.exists() or result.stdout)
        dest = Path('/tmp') / ('review-mvp2-' + uuid.uuid4().hex)
        self.addCleanup(remove_destination, dest)
        run = call(dest, extra=('--fixture', 'mvp2'))
        self.assertEqual(run.returncode, 0, run.stderr)
        sample = ROOT / 'examples/offline-review'
        self.assertEqual({p.name: p.read_bytes() for p in dest.iterdir()},
                         {p.name: p.read_bytes() for p in sample.iterdir()})
        self.assertNotEqual(json.loads((dest / 'MANIFEST.json').read_bytes())['subject']['graph_sha256'], STATE_GRAPH)

    def test_state_identity_authority_and_absent_behavioral_results(self):
        m = self.manifest
        self.assertEqual(set(self.files), PREVIEWS | {'README.md', 'MANIFEST.json'})
        self.assertEqual(m['subject']['graph_sha256'], STATE_GRAPH)
        self.assertEqual(m['subject']['fixture'], 'by_retain_and_sum')
        self.assertEqual(m['subject']['source_sha256'], {'main.sas': SOURCE_HASH})
        self.assertEqual(m['subject']['fixture_sha256'], EXPECTATIONS_HASH)
        self.assertEqual(sha256((ROOT / 'tests/p2a_expectations.py').read_bytes()).hexdigest(), EXPECTATIONS_HASH)
        self.assertEqual((m['source_consistency'], m['reconstruction_status'], m['stage_gate']),
                         ('PASSED', 'COMPLETE', 'BLOCKED'))
        self.assertEqual(m['behavioral_evidence'], 'UNAVAILABLE')
        self.assertEqual(m['full_workflow_gate'], 'BLOCKED')
        self.assertNotIn('tieout_counts', m)
        self.assertNotIn('case_table_sha256', m['subject'])
        for name, raw in self.files.items():
            for field, expected in STATUS.items():
                if name.endswith('.json'):
                    self.assertEqual(json.loads(raw)[field], expected)
                else:
                    self.assertIn(f'{field}: {expected}', raw.decode())
            self.assertNotRegex(raw.decode(), r'\bB(?:0[1-9]|1[0-7])\b|"verdict"\s*:\s*"PASS"')
        self.assertIn('No approved behavioral oracle', self.files['README.md'].decode())
        observed = self.command_result.stderr.decode().split('Observed stages: ')[1]
        self.assertIn('semantic.py:reconstruct', observed)
        self.assertIn('_dependency_diagnostics.py:diagnose', observed)
        self.assertIn('_draft_preview.py:generate_preview', observed)
        self.assertNotIn('build_report', observed)
        self.assertNotIn('render_review', observed)

    def test_state_facts_lineage_and_source_spans(self):
        modules = self.files['MODULES.md'].decode()
        for text in ('RETAIN `balance` with initialization `8`', 'FIRST.group', 'LAST.subkey',
                     'Sum statement `balance + amount`', 'prior retained state', 'ACROSS_ROWS',
                     'DECLARED_SYNTHETIC_INPUT', 'input phase', 'two-fixture-preview/1'):
            self.assertIn(text.lower(), modules.lower())
        source = PUBLIC_CASES['by_retain_and_sum']['files']['main.sas']
        self.assertEqual(sha256(source).hexdigest(), SOURCE_HASH)
        evidence = self.files['EVIDENCE.md'].decode()
        for start, end in re.findall(r'bytes \[(\d+), (\d+)\)', evidence):
            self.assertIn(sha256(source[int(start):int(end)]).hexdigest(), evidence)
        self.assertIn(source.decode(), self.files['README.md'].decode())
        self.assertIn('STATE_CONTINUITY', evidence)
        self.assertIn('NUMERIC_EQUIVALENCE_UNPROVED', evidence)
        self.assertIn('retained accumulation across rows', self.files['ARCHITECTURE.md'].decode())
        self.assertNotIn('STATE annotation as conservative', self.files['ARCHITECTURE.md'].decode())
        self.assertNotIn('join multiplicity', self.files['ADR_NATIVE.md'].decode())

    def test_deterministic_hashes_links_and_existing_destination(self):
        dest = free_destination()
        self.addCleanup(remove_destination, dest)
        second = call(dest, extra=('--fixture', 'by-retain-and-sum'))
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in dest.iterdir()}, self.files)
        receipt = json.loads(second.stdout)
        self.assertEqual(receipt['manifest_sha256'], sha256(self.files['MANIFEST.json']).hexdigest())
        for name, entry in self.manifest['files'].items():
            self.assertEqual(entry, {'bytes': len(self.files[name]), 'sha256': sha256(self.files[name]).hexdigest()})
        for owner, raw in self.files.items():
            if not owner.endswith('.md'):
                continue
            for link in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)', raw.decode()):
                url = urlsplit(link)
                self.assertFalse(url.scheme or url.netloc or url.query)
                target = unquote(url.path) or owner
                self.assertIn(target, self.files)
                if url.fragment:
                    headings = re.findall(r'^#{1,6} (.+)$', self.files[target].decode(), re.M)
                    anchors = {re.sub(r'[^\w-]', '', h.lower().replace(' ', '-')) for h in headings}
                    self.assertIn(unquote(url.fragment), anchors)
        refused = call(dest, extra=('--fixture', 'by-retain-and-sum'))
        self.assertEqual(refused.returncode, 2)
        self.assertFalse(refused.stdout)
        self.assertEqual({p.name: p.read_bytes() for p in dest.iterdir()}, self.files)

    def test_altered_state_declarations_refuse_before_execution_or_output(self):
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder)
            shutil.copytree(ROOT / 'scripts', clone / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
            (clone / 'tests').mkdir()
            declarations = clone / 'tests/p2a_expectations.py'
            declarations.write_bytes((ROOT / 'tests/p2a_expectations.py').read_bytes() + b'\nraise RuntimeError("ALTERED_SOURCE_EXECUTED")\n')
            dest = free_destination()
            self.addCleanup(remove_destination, dest)
            run = call(dest, script=clone / 'scripts/review_workflow.py', extra=('--fixture', 'by-retain-and-sum'))
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertNotIn(b'ALTERED_SOURCE_EXECUTED', run.stderr)
            self.assertFalse(run.stdout or dest.exists())

    def test_revised_renderer_keeps_sort_set_and_sql_contracts_distinct(self):
        from tempfile import TemporaryDirectory
        from mvp2_fixture import make_multi_module_case
        from sas_re._dependency_diagnostics import diagnose
        from sas_re._draft_preview import generate_preview, PreviewError
        from sas_re.evidence import digest
        with TemporaryDirectory() as folder:
            graph = make_multi_module_case(folder)[3]
        diagnostic = diagnose(graph, digest(graph))
        revised = generate_preview(graph, diagnostic, revision='tf1')
        for name in ('ADR_NATIVE.md', 'ADR_SPARK.md'):
            text = revised[name].decode()
            self.assertIn('tie freedom established by the SORT contract', text)
            self.assertIn('actual producer stream', text)
            self.assertIn('no invented secondary order', text)
        with self.assertRaises(PreviewError):
            generate_preview(graph, diagnostic, revision='unknown')
