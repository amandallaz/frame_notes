from django.contrib.auth import get_user_model
from django.test import TestCase

from studio.folder_import import set_frame_one
from studio.models import FilmRoll, FrameNote, Project


class SetFrameOneTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("tester", password="x")
        project = Project.objects.create(title="P", owner=user)
        self.roll = FilmRoll.objects.create(owner=user, label="R")
        self.roll.projects.add(project)
        for num in (-1, 0, 5, 6):
            FrameNote.objects.create(roll=self.roll, frame_number=num, note=str(num))

    def test_scan_at_frame_5_becomes_frame_one(self):
        delta = set_frame_one(self.roll, source_frame_number=5)
        self.assertEqual(delta, -4)
        numbers = list(
            self.roll.frames.order_by("frame_number").values_list(
                "frame_number", flat=True
            )
        )
        self.assertEqual(numbers, [-5, -4, 1, 2])

    def test_already_frame_one(self):
        FrameNote.objects.create(roll=self.roll, frame_number=1, note="one")
        self.assertEqual(set_frame_one(self.roll, source_frame_number=1), 0)
