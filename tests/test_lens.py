import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('lens', str(ROOT / 'agentdaemon-lens'))
spec = importlib.util.spec_from_loader(loader.name, loader)
lens = importlib.util.module_from_spec(spec)
loader.exec_module(lens)


class LensTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(os.path.realpath(self.tmp.name))
        self.base = self.root / 'app-server-daemon' / 'releases'
        self.base.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def release(self, name='v1'):
        p = self.base / name
        p.mkdir()
        (p / 'codex').write_bytes(b'abc')
        return p

    def test_sizes(self):
        self.release(); self.release('v2')
        row = lens.inventory(self.root)[0]
        self.assertEqual((row['release_directories'], row['logical_bytes']), (2, 6))
        self.assertEqual(row['state'], 'OBSERVED')

    def test_missing(self):
        self.assertEqual(lens.inventory(self.root)[1]['state'], 'NOT_OBSERVED')

    def test_empty_observed(self):
        self.assertEqual(lens.inventory(self.root)[0]['state'], 'OBSERVED')

    def test_links_not_followed(self):
        p = self.release()
        (p / 'private-link').symlink_to(self.root)
        row = lens.inventory(self.root)[0]
        self.assertEqual(row['skipped_links'], 1)
        self.assertEqual(row['logical_bytes'], 3)

    def test_symlink_root_unknown(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.root)
        self.assertEqual(lens.inventory(alias)[0]['state'], 'UNKNOWN')

    def test_hardlinks_count_once(self):
        p = self.release()
        os.link(p / 'codex', p / 'alias')
        self.assertEqual(lens.inventory(self.root)[0]['logical_bytes'], 3)

    def test_entry_bound(self):
        self.release()
        self.assertEqual(lens.inventory(self.root, max_entries=0)[0]['state'], 'UNKNOWN')

    def test_permission_failure(self):
        with patch.object(lens.os, 'scandir', side_effect=PermissionError):
            self.assertEqual(lens.inventory(self.root)[0]['state'], 'UNKNOWN')

    def test_process_matching(self):
        text = '/generic/codex app-server --managed-daemon\n/generic/codex app-server daemon pid-update-loop\nsh -c codex app-server --managed-daemon\n'
        self.assertEqual(lens.process_clues(text), {'state': 'OBSERVED', 'managed_daemon_matches': 1, 'updater_matches': 1})

    def test_no_raw_values(self):
        self.release('PRIVATE_SECRET')
        output = json.dumps(lens.inventory(self.root))
        self.assertNotIn('PRIVATE_SECRET', output)
        self.assertNotIn(str(self.root), output)

    def test_offline_user_path(self):
        self.release(); self.release('v2')
        saved = self.root / 'processes.txt'
        saved.write_text('/generic/codex app-server --managed-daemon\n')
        command = [sys.executable, str(ROOT / 'agentdaemon-lens'), '--packages-root', str(self.root), '--process-file', str(saved), '--json', '--check']
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(json.loads(run.stdout)['processes']['managed_daemon_matches'], 1)

    def test_offline_does_not_run_ps(self):
        saved = self.root / 'processes.txt'; saved.write_text('')
        with patch.object(sys, 'argv', ['lens', '--packages-root', str(self.root), '--process-file', str(saved)]), patch.object(lens.subprocess, 'run', side_effect=AssertionError('live probe')):
            self.assertEqual(lens.main(), 0)

    def test_fifo_rejected(self):
        fifo = self.root / 'fifo'; os.mkfifo(fifo)
        with self.assertRaises(ValueError): lens.read_process_file(fifo)

    def test_oversize_rejected(self):
        source = self.root / 'large'; source.write_bytes(b'x' * 2000001)
        with self.assertRaises(ValueError): lens.read_process_file(source)

    def test_file_instead_directory_unknown(self):
        (self.root / 'standalone').mkdir()
        (self.root / 'standalone' / 'releases').write_text('wrong type')
        self.assertEqual(lens.inventory(self.root)[1]['state'], 'UNKNOWN')


    def snapshot(self):
        return {'schema_version': 1, 'packages': lens.inventory(self.root)}

    def test_comparison_growth_and_decrease(self):
        before = self.snapshot()
        self.release()
        after = self.snapshot()
        row = lens.compare_snapshots(before, after)['packages'][0]
        self.assertEqual((row['release_directories_delta'], row['logical_bytes_delta']), (1, 3))
        self.assertEqual(lens.compare_snapshots(after, before)['packages'][0]['logical_bytes_delta'], -3)

    def test_comparison_absence_and_reordered_families(self):
        before = self.snapshot()
        after = self.snapshot(); after['packages'].reverse()
        result = lens.compare_snapshots(before, after)
        self.assertEqual(result['packages'][1]['state'], 'COMPARABLE')
        self.assertEqual(result['packages'][1]['logical_bytes_delta'], 0)

    def test_comparison_unknown_and_skipped_links(self):
        for field, value in [('state', 'UNKNOWN'), ('skipped_links', 1)]:
            before, after = self.snapshot(), self.snapshot()
            after['packages'][0][field] = value
            row = lens.compare_snapshots(before, after)['packages'][0]
            self.assertEqual(row['state'], 'UNKNOWN')
            self.assertIsNone(row['logical_bytes_delta'])

    def test_comparison_invalid_inputs(self):
        import copy
        good = self.snapshot()
        invalid = [None, [], {}, {'schema_version': True}, {'schema_version': 2}]
        for key, value in [('logical_bytes', -1), ('logical_bytes', True), ('logical_bytes', '3'), ('logical_bytes', 1.5), ('logical_bytes', 2**63), ('state', 'made-up'), ('family', []), ('family', 'private')]:
            bad = copy.deepcopy(good); bad['packages'][0][key] = value; invalid.append(bad)
        bad = copy.deepcopy(good); bad['packages'][1] = bad['packages'][0]; invalid.append(bad)
        bad = copy.deepcopy(good); bad['packages'][1]['logical_bytes'] = 3; invalid.append(bad)
        bad = copy.deepcopy(good); del bad['packages'][0]['regular_files']; invalid.append(bad)
        for bad in invalid:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                lens.compare_snapshots(good, bad)

    def test_comparison_does_not_echo_extra_values(self):
        before, after = self.snapshot(), self.snapshot()
        after['private'] = 'PRIVATE_SECRET'; after['packages'][0]['path'] = 'PRIVATE_SECRET'
        self.assertNotIn('PRIVATE_SECRET', json.dumps(lens.compare_snapshots(before, after)))

    def compare_cli(self, before, after, *extra):
        a, b = self.root / 'before.json', self.root / 'after.json'
        a.write_text(json.dumps(before)); b.write_text(json.dumps(after))
        return subprocess.run([sys.executable, str(ROOT / 'agentdaemon-lens'), '--compare', str(a), str(b), '--json', '--check', *extra], capture_output=True, text=True)

    def test_comparison_cli_check_codes(self):
        before = self.snapshot()
        self.assertEqual(self.compare_cli(before, before).returncode, 0)
        self.release()
        after = self.snapshot()
        run = self.compare_cli(before, after)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(json.loads(run.stdout)['packages'][0]['logical_bytes_delta'], 3)
        after['packages'][1]['state'] = 'UNKNOWN'
        self.assertEqual(self.compare_cli(before, after).returncode, 2)

    def test_comparison_invalid_cli_no_traceback_or_values(self):
        run = self.compare_cli(self.snapshot(), {'private': 'PRIVATE_SECRET'})
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, '')
        self.assertNotIn('PRIVATE_SECRET', run.stderr)
        self.assertNotIn('Traceback', run.stderr)

    def test_comparison_no_live_probes(self):
        a = self.root / 'saved.json'; a.write_text(json.dumps(self.snapshot()))
        with patch.object(sys, 'argv', ['lens', '--compare', str(a), str(a)]), patch.object(lens.subprocess, 'run', side_effect=AssertionError('live probe')), patch.object(lens, 'inventory', side_effect=AssertionError('filesystem inventory')):
            self.assertEqual(lens.main(), 0)

    def test_comparison_rejects_acquisition_flags(self):
        for flags in [('--packages-root', '.'), ('--process-file', 'x'), ('--no-processes',)]:
            run = self.compare_cli(self.snapshot(), self.snapshot(), *flags)
            self.assertEqual(run.returncode, 2)

    def test_symlink_saved_input_rejected(self):
        source = self.root / 'source'; source.write_text('{}')
        alias = self.root / 'alias'; alias.symlink_to(source)
        with self.assertRaises(ValueError): lens.read_process_file(alias)


if __name__ == '__main__':
    unittest.main()
