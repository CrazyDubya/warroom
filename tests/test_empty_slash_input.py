"""Real mounted Input/Enter incomplete slash lifecycle, no helper-only dispatch."""
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
from textual.widgets import Input


class EmptySlashInput(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='warroom-slash-test-')
        self.addCleanup(self.temp.cleanup)
        self.state_path = Path(self.temp.name) / 'state.json'
        self.attempts = []
        def blocked(*args, **kwargs):
            self.attempts.append(1)
            raise AssertionError('Network prohibited')
        self.addCleanup(patch.stopall)
        patch.object(socket.socket, 'connect', blocked).start()
        patch.object(socket, 'create_connection', blocked).start()

    async def submit(self, app, pilot, command):
        field = app.query_one('#command-input', Input)
        field.focus()
        field.value = command
        await pilot.press('enter')
        await pilot.pause()
        self.assertEqual(field.value, '')
        self.assertEqual(self.attempts, [])

    async def exercise(self, command, screenshot=None):
        app = WarRoomApp(state_path=self.state_path)
        async with app.run_test(size=(130, 45)) as pilot:
            await pilot.pause()
            before = app.state.model_dump(mode='json')
            await self.submit(app, pilot, command)
            self.assertEqual(app.state.model_dump(mode='json'), before)
            await self.submit(app, pilot, '+Synthetic after incomplete slash')
            self.assertEqual(app.state.active_focus.evidence[-1].title, 'Synthetic after incomplete slash')
            if screenshot and os.environ.get('WARROOM_SCREENSHOTS'):
                folder = Path(os.environ['WARROOM_SCREENSHOTS'])
                folder.mkdir(parents=True, exist_ok=True)
                app.save_screenshot(str(folder / (screenshot + '.svg')))
        self.assertTrue(self.state_path.exists())
        reopened = WarRoomApp(state_path=self.state_path)
        async with reopened.run_test(size=(130, 45)) as pilot:
            await pilot.pause()
            self.assertEqual(reopened.state.active_focus.evidence[-1].title, 'Synthetic after incomplete slash')
        self.assertEqual(self.attempts, [])

    async def test_bare_slash_survives_then_normal_input_saves_and_reopens(self):
        await self.exercise('/', 'after-bare-slash')

    async def test_slash_whitespace_survives_then_normal_input_saves_and_reopens(self):
        await self.exercise('/   ')

    async def test_blank_and_unknown_nonempty_commands_stay_tolerated(self):
        await self.exercise('')
        await self.exercise('/synthetic-unknown')

    async def test_recognized_new_and_save_commands_stay_unchanged(self):
        app = WarRoomApp(state_path=self.state_path)
        async with app.run_test(size=(130, 45)) as pilot:
            await pilot.pause()
            await self.submit(app, pilot, '/new Synthetic Slash Control')
            self.assertEqual(app.state.active_focus.name, 'Synthetic Slash Control')
            await self.submit(app, pilot, '+Synthetic recognized control')
            await self.submit(app, pilot, '/save')
        reopened = WarRoomApp(state_path=self.state_path)
        async with reopened.run_test(size=(130, 45)) as pilot:
            await pilot.pause()
            self.assertEqual(reopened.state.active_focus.name, 'Synthetic Slash Control')
            self.assertEqual(reopened.state.active_focus.evidence[-1].title, 'Synthetic recognized control')
