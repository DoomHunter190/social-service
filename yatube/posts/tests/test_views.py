import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.cache import cache

from ..models import Post, Group, Comment, Follow

TEST_OF_POST: int = 13
FIRST_OF_POSTS: int = 10
SECOND_OF_POSTS: int = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.user2 = User.objects.create_user(username='TestUser2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_correct_template(self):
        """URL - address matching patterns."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def assert_post_response(self, response):
        """Correct context post."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def assert_response_context(self, response):
        """Correct context response."""
        post_text = {
            response.context['page_obj'][0]: self.post,
            response.context['page_obj'][0].group: self.group,
            response.context['page_obj'][0].author: self.user.username,
            response.context['page_obj'][0].image: self.post.image}
        for value, expected in post_text.items():
            self.assertEqual(post_text[value], expected)

    def test_post_create_page_show_correct_context(self):
        """Create_post template correct context."""
        response = self.authorized_client.get(reverse('posts:create_post'))
        self.assert_post_response(response)

    def test_post_edit_page_show_correct_context(self):
        """Post_edit template correct context."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assert_post_response(response)

    def test_post_list_page_show_correct_context(self):
        """Index template correct context."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assert_response_context(response)
        self.assertIn(self.post, response.context['page_obj'],
                      'поста нет на главной странице')

    def test_post_group_list_page_show_correct_context(self):
        """Group_list template correct context."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assert_response_context(response)
        self.assertEqual(self.group, response.context['group'])
        self.assertIn(self.post, response.context['page_obj'],
                      'поста нет в группе')

    def test_post_detail_page_show_correct_context(self):
        """Post_detail template correct context."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_text = {response.context['post'].text: 'Тестовый пост',
                     response.context['post'].group: self.group,
                     response.context['post'].author: self.user.username,
                     response.context['post'].image: self.post.image}
        for value, expected in post_text.items():
            self.assertEqual(post_text[value], expected)

    def test_post_profile_page_show_correct_context(self):
        """Profile template correct context."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))
        self.assert_response_context(response)
        self.assertEqual(self.user, response.context['author'])
        self.assertIn(self.post, response.context['page_obj'],
                      'поста нет в профиле')

    def test_post_added_correctly_user2(self):
        """
        The post has not been added to another user,
        is available on the Index page, group.
        """
        group2 = Group.objects.create(title='Тестовая группа 2',
                                      slug='test_group2')
        post = Post.objects.create(
            text='Тестовый пост от другого автора',
            author=self.user2,
            group=group2)
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))
        response_group = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        self.assertNotIn(post, group, 'поста нет в другой группе')
        self.assertNotIn(post, profile,
                         'поста нет в группе другого пользователя')

    def test_create_comment(self):
        """Authorized user can create comments."""
        comment_count = Comment.objects.count()
        new_comment = (Comment.objects.create(
            post=self.post,
            author=self.user, text='Пробный комментарий')).text
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}))
        comment_1 = response.context['comments'][0].text
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(comment_1, new_comment)

    def test_index_cache(self):
        """Test cache."""
        new_post = Post.objects.create(
            text='Комментарий проверки кэша',
            author=self.user,
            group=self.group
        )
        current_content = self.authorized_client.get(
            reverse('posts:index')
        ).content
        new_post.delete()
        after_delete_post_content = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(current_content, after_delete_post_content)
        cache.clear()
        after_clear_cache_content = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(
            current_content, after_clear_cache_content
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug',
            description='Тестовое описание')
        cls.posts = []
        for i in range(TEST_OF_POST):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        """10 posts on the first page."""
        list_urls = {
            reverse('posts:index'): 'index',
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}): 'group',
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}): 'profile',
        }
        for url in list_urls.keys():
            response = self.client.get(url)
            self.assertEqual(len(response.context['page_obj']), FIRST_OF_POSTS)

    def test_second_page_contains_three_posts(self):
        """3 posts on the second page."""
        list_urls = {
            reverse('posts:index') + '?page=2': 'index',
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}) + '?page=2':
            'group',
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}) + '?page=2':
            'profile',
        }
        for url in list_urls.keys():
            response = self.client.get(url)
            self.assertEqual(len(response.context['page_obj']),
                             SECOND_OF_POSTS)


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower',)
        self.user_following = User.objects.create_user(username='following',)
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        """Follow test."""
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)
        self.assertIsNotNone(Follow.objects.first())

    def test_unvollow(self):
        """Unfollow test."""
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription(self):
        """
        The user record is not visible to those who are not subscribed to it.
        """
        response = self.client_auth_follower.get(
            reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
