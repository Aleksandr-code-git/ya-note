from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(
            username='Vlad'
        )
        cls.commoner = User.objects.create(
            username='Aleksandr'
        )
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

    def test_pages_availability_authorised(self):
        self.client.force_login(self.commoner)
        urls = (
            'notes:add',
            'notes:list',
            'notes:success',
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_anonymous(self):
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                if name == 'users:logout':
                    response = self.client.post(url)
                else:
                    response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_notes(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.commoner, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in (
                'notes:edit',
                'notes:delete',
                'notes:detail',
            ):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        login_url = reverse('users:login')
        for name, args in (
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:add', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:list', None),
            ('notes:success', None),
        ):
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
