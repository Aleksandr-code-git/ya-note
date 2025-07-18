from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestNotes(TestCase):
    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(
            username='Petya'
        )
        notes = [
            Note(
                title=f'Заметка {index}',
                text='Просто текст.',
                author=cls.author,
                slug=f'unique-slug-{index}'
            )
            for index in range(0, 10)
        ]
        Note.objects.bulk_create(notes)
        cls.a_note = Note.objects.create(
            title='Name',
            text='Something',
            author=cls.author,
        )
        cls.other_user = User.objects.create(
            username='Vasya'
        )

    def test_note_in_note_list(self):
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        old_object_list = response.context['object_list']
        old_notes_count = old_object_list.count()

        self.new_note = Note.objects.create(
            title='Название',
            text='Text',
            author=self.author,
        )

        response = self.client.get(self.LIST_URL)
        new_object_list = response.context['object_list']
        new_notes_count = new_object_list.count()
        self.assertEqual(old_notes_count + 1, new_notes_count)

    def test_note_ownership(self):
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        original_authors_list = response.context['object_list']

        self.other_users_note = Note.objects.create(
            title='MAGICAL TITLE',
            text='MAGICAL TEXT',
            author=self.other_user,
        )

        self.assertNotIn(self.other_users_note, original_authors_list)

    def test_edit_and_create_form(self):
        self.client.force_login(self.author)
        for name, args in (
            ('notes:add', None),
            ('notes:edit', (self.a_note.slug,)),
        ):
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
