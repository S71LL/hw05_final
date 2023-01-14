from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache
import tempfile
import shutil

from posts.models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.another_user = User.objects.create_user(username='author')
        cls.unfollow_user = User.objects.create_user(username='unfoll')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.author_post = Post.objects.create(
            author=cls.another_user,
            text='Пост автора',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )
        cls.another_group = Group.objects.create(
            title='Тестовая группа',
            slug='another-test-slug',
            description='Тестовое описание',
        )
        cls.another_post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.another_group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            text='Коммент',
            post=cls.post,
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_unfollow_client = Client()
        self.authorized_unfollow_client.force_login(self.unfollow_user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_create.html',
        }
        for reverse_name, templates in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, templates)

    def test_home_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, 'Тестовый пост')
        self.assertEqual(first_object.author.username, 'auth')
        self.assertIsNotNone(first_object.image)

    def test_group_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        post_group_0 = first_object.group.title
        post_img_0 = first_object.image
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertIsNotNone(post_img_0)

    def test_user_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_img_0 = first_object.image
        self.assertEqual(post_author_0, 'auth')
        self.assertIsNotNone(post_img_0)

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_object = response.context['post']
        post_id_0 = post_object.id
        post_img_0 = post_object.image
        post_comment_0 = response.context['comments'][0].text
        self.assertEqual(post_id_0, self.post.id)
        self.assertIsNotNone(post_img_0)
        self.assertEqual(post_comment_0, 'Коммент')

    def test_post_create_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expeceted in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expeceted)

    def test_post_edit_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['is_edit'], True)
        self.assertEqual(response.context['post_id'], self.post.id)

    def test_index_page_cache(self):
        cached_page = self.authorized_client.get(
            reverse('posts:index')).content
        Post.objects.create(text='Новый пост', author=self.user)
        response = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(cached_page, response)
        cache.clear()
        updated_response = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(cached_page, updated_response)

    def test_following(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.another_user.username}))
        self.assertTrue(
            Follow.objects.filter(user_id=self.user.id,
                                  author_id=self.another_user.id))

    def test_unfollow(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.another_user.username}))
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.another_user.username}))
        self.assertFalse(
            Follow.objects.filter(user_id=self.user.id,
                                  author_id=self.another_user.id).exists())

    def test_new_post_of_author_in_newsline(self):
        request = self.authorized_unfollow_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(len(request.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for id in range(13):
            cls.post = Post.objects.create(
                id=id,
                author=cls.user,
                text='Тестовый пост',
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_posts(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_posts(self):
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_of_group_contains_ten_posts(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_of_group_contains_three_posts(self):
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2',)
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_of_user_contains_ten_posts(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_of_user_contains_three_posts(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
            + '?page=2',)
        self.assertEqual(len(response.context['page_obj']), 3)
