from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..models import Post, Group
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.user1 = User.objects.create_user(username='UserTest')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug='test-slug',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client.force_login(self.user1)

    def test_urls_guest_user(self):
        """Pages are available to everyone."""
        template_urls = {
            'index': '',
            'group': f'/group/{self.group.slug}/',
            'profile': f'/profile/{self.user.username}/',
            'posts': f'/posts/{self.post.id}/',
        }
        for url in template_urls:
            response = self.guest_client.get(template_urls[url])
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect(self):
        """Unauthorized user is redirected to Login.html."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_urls_authorized_user(self):
        """Creating a post only by an authorized user."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL - address matches pattern."""
        templates_url_names = {
            'posts/index.html': '',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
            'posts/create_post.html': '/create/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_not_found(self):
        """Page not found."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_edit_post(self):
        """Edit post by author only."""
        response = self.guest_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
