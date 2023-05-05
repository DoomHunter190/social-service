from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Works correctly in the model __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_post_name = post.text
        expected_group_name = group.title
        self.assertEqual(expected_post_name, str(post))
        self.assertEqual(expected_group_name, str(group))
