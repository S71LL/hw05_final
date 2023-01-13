from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, который длиннее 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        group = self.group
        expected_post_string = post.text[:15]
        expected_group_string = group.title
        self.assertEqual(expected_post_string, str(post))
        self.assertEqual(expected_group_string, str(group))

    def test_verbos_name(self):
        post = self.post
        field_verboses = {
            'text': 'Текст поста',
            'created': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        post = self.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относится пост'
        }
        for field, expected_values in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_values)
