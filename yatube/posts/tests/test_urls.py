from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = self.client

    def test_homepage(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.another_user = User.objects.create_user(username='anotherAuth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = self.client
        self.authorized_client = Client()
        self.another_autorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_autorized_client.force_login(self.another_user)

    def test_urls_uses_correct_template(self):
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
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, teamplate in templates_url_names.items():
            with self.subTest(address=address):
                responce = self.authorized_client.get(address)
                self.assertTemplateUsed(responce, teamplate)

    def test_posts_url_exists_at_desired_location_authorized(self):
        templates_codes = {
            reverse('posts:post_create'): HTTPStatus.FOUND,
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}): HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for adress, status_code in templates_codes.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_post_create_url_redirect_anonymous_on_login(self):
        response = self.guest_client.get(reverse('posts:post_create'),
                                         follow=True)
        expected_url = (reverse('users:login') + '?next='
                        + reverse('posts:post_create'))
        self.assertRedirects(response, expected_url)

    def test_post_comment_url_redirect_anonymous_on_login(self):
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            follow=True
        )
        expected_url = (reverse('users:login') + '?next='
                        + reverse('posts:add_comment',
                                  kwargs={'post_id': self.post.id}))
        self.assertRedirects(response, expected_url)
