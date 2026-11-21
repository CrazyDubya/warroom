"""Real mounted app input/save/reopen regressions, no control-widget injection."""
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('WARROOM_SOURCE', Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT))
from warroom.app import WarRoomApp
from warroom.ui.widgets import EvidenceItem, WitnessBox
from textual.widgets import Input, Static


class ActiveFocusChildren(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='warroom-children-test-')
        self.addCleanup(self.temp.cleanup)
        self.state_path = Path(self.temp.name) / 'state.json'
        self.attempts = []
        def blocked(*args, **kwargs):
            self.attempts.append(1)
            raise AssertionError('Network prohibited in full app fixture')
        self.addCleanup(patch.stopall)
        patch.object(socket.socket, 'connect', blocked).start()
        patch.object(socket, 'create_connection', blocked).start()

    async def submit(self, app, pilot, command):
        field = app.query_one('#command-input', Input)
        field.focus()
        field.value = command
        await pilot.press('enter')
        await pilot.pause()

    def assert_matches_active(self, app):
        focus = app.state.active_focus
        self.assertEqual([w.evidence.title for w in app.query(EvidenceItem)],
                         [e.title for e in focus.evidence[:5]])
        self.assertEqual([w.witness_type for w in app.query(WitnessBox)], focus.witnesses[:4])
        self.assertEqual(self.attempts, [])

    def screenshot(self, app, name):
        output = os.environ.get('WARROOM_SCREENSHOTS')
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
            app.save_screenshot(str(Path(output) / (name + '.svg')))

    async def test_demo_hydrates_existing_evidence_and_witness_children(self):
        app = WarRoomApp(state_path=self.state_path)
        async with app.run_test(size=(130, 45)) as pilot:
            await pilot.pause()
            self.assertEqual(len(app.state.active_focus.evidence), 2)
            self.assert_matches_active(app)
            self.assertEqual(len(app.query(WitnessBox)), 4)
            self.screenshot(app, 'demo')

    async def test_input_add_saves_and_reopen_displays_same_three_items(self):
        app = WarRoomApp(state_path=self.state_path)
        async with app.run_test(size=(130, 45)) as pilot:
            await pilot.pause()
            await self.submit(app, pilot, '+Synthetic pinned evidence')
            self.assertEqual(len(app.state.active_focus.evidence), 3)
            self.assert_matches_active(app)
            self.screenshot(app, 'after-add')
        self.assertTrue(self.state_path.exists())
        reopened = WarRoomApp(state_path=self.state_path)
        async with reopened.run_test(size=(130, 45)) as pilot:
            await pilot.pause()
            self.assertEqual(len(reopened.state.active_focus.evidence), 3)
            self.assertEqual(reopened.state.active_focus.evidence[-1].title, 'Synthetic pinned evidence')
            self.assert_matches_active(reopened)
            self.screenshot(reopened, 'reopened')

    async def test_focus_commands_replace_previous_children_and_empty_placeholders(self):
        app = WarRoomApp(state_path=self.state_path)
        async with app.run_test(size=(130, 45)) as pilot:
            await pilot.pause()
            await self.submit(app, pilot, '/focus Auth Bug')
            self.assertEqual(app.state.active_focus.name, 'Auth Bug Investigation')
            self.assert_matches_active(app)
            self.assertEqual(len(app.query(WitnessBox)), 2)
            self.screenshot(app, 'switched')
            await self.submit(app, pilot, '/new Synthetic Empty')
            self.assertEqual(app.state.active_focus.name, 'Synthetic Empty')
            self.assertEqual(len(app.state.active_focus.evidence), 0)
            self.assert_matches_active(app)
            rendered = [str(w.render()) for w in app.query_one('#evidence-board').query(Static)]
            self.assertTrue(any('No evidence pinned yet' in text for text in rendered))
            await self.submit(app, pilot, '+First new focus evidence')
            self.assert_matches_active(app)
            self.assertEqual(len(app.query(EvidenceItem)), 1)

    async def test_existing_five_evidence_and_four_witness_caps_are_preserved(self):
        app = WarRoomApp(state_path=self.state_path)
        async with app.run_test(size=(130, 45)) as pilot:
            await pilot.pause()
            for number in range(5):
                await self.submit(app, pilot, '+Synthetic capped evidence ' + str(number))
            for name in ['GARDENER', 'SCRIBE']:
                await self.submit(app, pilot, '/witness ' + name)
            self.assertEqual(len(app.state.active_focus.evidence), 7)
            self.assertEqual(len(app.state.active_focus.witnesses), 6)
            self.assert_matches_active(app)
            self.assertEqual(len(app.query(EvidenceItem)), 5)
            self.assertEqual(len(app.query(WitnessBox)), 4)
            rendered = [str(w.render()) for w in app.query_one('#evidence-board').query(Static)]
            self.assertTrue(any('+2 more...' in text for text in rendered))
            self.screenshot(app, 'caps')
