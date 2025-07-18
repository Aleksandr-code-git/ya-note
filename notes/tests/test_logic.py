from http import HTTPStatus

from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

# Импортируем из файла с формами список стоп-слов и предупреждение формы.
# Загляните в news/forms.py, разберитесь с их назначением.
from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    title = 'TITLE'
    text = 'TEXT'
    slug = 'SLUG'

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='Danya')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

    def test_anonymous_user_cant_create_note(self):
        self.client.post(
            self.url,
            data={
                'title': 'TITLE',
                'text': 'TEXT',
            }
        )
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_can_create_note(self):
        self.auth_client.post(
            self.url,
            data={
                'title': 'TITLE',
                'text': 'TEXT',
            }
        )
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.title)
        self.assertEqual(note.text, self.text)
        self.assertEqual(note.author, self.user)

    def test_cant_create_notes_with_the_same_slug(self):
        notes_data = [
            {'title': 'TITLE', 'text': 'TEXT', 'slug': 'same_slug'},
            {'title': 'some_title', 'text': 'some_text', 'slug': 'same_slug'}
        ]
        response1 = self.auth_client.post(self.url, data=notes_data[0])
        self.assertEqual(response1.status_code, HTTPStatus.FOUND)
        response2 = self.auth_client.post(self.url, data=notes_data[1])
        form = response2.context['form']
        self.assertFormError(
            form=form,
            field='slug',
            errors=f'same_slug{WARNING}'
        )

    def test_slug_autogeneration(self):
        with patch('notes.models.slugify') as mock_slug:
            mock_slug.return_value = 'some_slug'
            note = Note.objects.create(
                title='some_title',
                text='some_text',
                author=self.user
            )
            self.assertEqual(note.slug, 'some_slug')


class TestNoteEditDelete(TestCase):
    NEW_NOTE_TEXT = 'extra_ordinary_text'
    OLD_NOTE_TEXT = 'test_text'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(
            username='Bayarin'
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(
            username='Prostoludin'
        )
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='test_title',
            text=cls.OLD_NOTE_TEXT,
            author=cls.author,
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.url_to_note = reverse('notes:detail', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')
        cls.form_data = {
            'title': cls.note.title, 'text': cls.NEW_NOTE_TEXT
        }

    def test_author_can_edit_his_notes(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_reader_cant_edit_others_notes(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.OLD_NOTE_TEXT)

    def test_author_can_delete_notes(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_reader_cant_delete_others_notes(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
