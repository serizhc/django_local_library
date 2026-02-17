from datetime import date, timedelta

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from catalog.models import Author, Book, BookInstance, Genre, Language


class ModelCoverageAdditionalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.genre = Genre.objects.create(name="Sci-Fi")
        cls.lang = Language.objects.create(name="English")
        cls.author = Author.objects.create(first_name="Isaac", last_name="Asimov")

        cls.book = Book.objects.create(
            title="I, Robot",
            author=cls.author,
            summary="Robots!",
            isbn="1234567890123",
            language=cls.lang,
        )
        cls.book.genre.add(cls.genre)

    def test_genre_str(self):
        self.assertEqual(str(self.genre), "Sci-Fi")

    def test_language_str(self):
        self.assertEqual(str(self.lang), "English")

    def test_book_str(self):
        self.assertEqual(str(self.book), "I, Robot")

    def test_book_display_genre(self):
        disp = self.book.display_genre()
        self.assertIn("Sci-Fi", disp)

    def test_author_str(self):
        self.assertEqual(str(self.author), "Asimov, Isaac")

    def test_author_absolute_url_format(self):
        url = self.author.get_absolute_url()
        self.assertTrue(url.startswith("/catalog/author/"))
        self.assertTrue(url.endswith("/"))

    def test_bookinstance_is_overdue_true_and_false(self):
        inst_ok = BookInstance.objects.create(
            book=self.book,
            imprint="1st",
            due_back=date.today() + timedelta(days=1),
            status="o",
        )
        inst_over = BookInstance.objects.create(
            book=self.book,
            imprint="1st",
            due_back=date.today() - timedelta(days=1),
            status="o",
        )
        self.assertFalse(inst_ok.is_overdue)
        self.assertTrue(inst_over.is_overdue)

    def test_bookinstance_str(self):
        inst = BookInstance.objects.create(
            book=self.book,
            imprint="1st",
            due_back=date.today(),
            status="a",
        )
        self.assertIn("I, Robot", str(inst))


class RenewBookViewAdditionalTests(TestCase):
    """Cubrir ramas no ejecutadas de renew_book_librarian."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="librarian2", password="pass12345")
        perm = Permission.objects.get(codename="can_mark_returned")
        cls.user.user_permissions.add(perm)

        cls.genre = Genre.objects.create(name="Horror")
        cls.lang = Language.objects.create(name="Spanish")
        cls.author = Author.objects.create(first_name="Stephen", last_name="King")
        cls.book = Book.objects.create(
            title="The Shining",
            author=cls.author,
            summary="Overlook",
            isbn="9999999999999",
            language=cls.lang,
        )
        cls.book.genre.add(cls.genre)

        cls.bookinst = BookInstance.objects.create(
            book=cls.book,
            imprint="2nd",
            due_back=date.today() + timedelta(days=7),
            status="o",
        )

    def test_renew_view_get_ok(self):
        self.client.login(username="librarian2", password="pass12345")
        url = reverse("renew-book-librarian", kwargs={"pk": self.bookinst.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_renew_view_post_past_date_shows_form_again(self):
        self.client.login(username="librarian2", password="pass12345")
        url = reverse("renew-book-librarian", kwargs={"pk": self.bookinst.pk})
        resp = self.client.post(url, {"renewal_date": date.today() - timedelta(days=1)})
        self.assertEqual(resp.status_code, 200)  # vuelve a renderizar formulario

    def test_renew_view_post_too_far_future_shows_form_again(self):
        # Algunos tutoriales validan que no sea > 4 semanas.
        self.client.login(username="librarian2", password="pass12345")
        url = reverse("renew-book-librarian", kwargs={"pk": self.bookinst.pk})
        resp = self.client.post(url, {"renewal_date": date.today() + timedelta(days=60)})
        self.assertEqual(resp.status_code, 200)

    def test_renew_view_post_valid_date_redirects(self):
        self.client.login(username="librarian2", password="pass12345")
        url = reverse("renew-book-librarian", kwargs={"pk": self.bookinst.pk})
        resp = self.client.post(url, {"renewal_date": date.today() + timedelta(days=14)})
        self.assertEqual(resp.status_code, 302)  # redirección


class PopulateCatalogAdditionalTests(TestCase):
    """
    Subir coverage de populate_catalog.py ejecutando sus funciones
    """
    def test_populate_catalog_functions_run(self):
        import populate_catalog as pc

        pc.clean_db()

        if hasattr(pc, "populate"):
            pc.populate()
        else:
            if hasattr(pc, "create_genres"):
                pc.create_genres()
            if hasattr(pc, "create_authors"):
                pc.create_authors()
            if hasattr(pc, "create_books"):
                pc.create_books()
            if hasattr(pc, "create_book_instances"):
                pc.create_book_instances()

        self.assertTrue(Author.objects.exists())
        self.assertTrue(Book.objects.exists())
