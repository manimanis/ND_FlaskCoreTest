import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Book

import random

BOOKS_PER_SHELF = 8
BOOKS_COUNT = 10

BOOKS_TITLES = [
    'Beginner Guide using Python, Pandas, NumPy, Scikit-Learn, IPython, TensorFlow and Matplotlib',
    'Data Analysis and Science Using Pandas, matplotlib, and the Python Programming Language',
    'Beginning Progressive Web App Development_ Creating a Native App Experience on the Web',
    'C Programming Absolute Beginner',
    'Cake PHP Cookbook',
    'Data Analysis From Scratch With Python- Beginner Guide using Python, Pandas, NumPy, Scikit-Learn, IPython, TensorFlow and Matplotlib'
]

BOOKS_AUTHORS = [
    'Karim Rjab',
    'Ahmed Belhassen',
    'Lazhar Zouari',
    'Anis Mekki',
    'Ahmed Bououni',
    'Nizar Dhifallah'
]

class BookTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "bookshelf_test"
        self.database_path = "postgresql://{}:{}@{}/{}".format('student', 'student', 'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        self.new_book = {
            'title': 'Anansi Boys',
            'author': 'Neil Gaiman',
            'rating': 5
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy(self.app)
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

        # Make sure we have only BOOKS_COUNT in our database
        books_count = self.db.session.query(Book).count()
        if books_count < BOOKS_COUNT:
            self.insertBooks(self.createRandomBooks(BOOKS_COUNT - books_count))
        elif books_count > BOOKS_COUNT:
            self.deleteAllBooks()
            self.insertBooks(self.createRandomBooks(BOOKS_COUNT))
    
    def tearDown(self):
        """Executed after reach test"""
        #self.deleteAllBooks()
        pass

    def createRandomBook(self):
        return Book(title=random.choice(BOOKS_TITLES), author=random.choice(BOOKS_AUTHORS), rating=random.randint(1, 5))

    def createRandomBooks(self, count=5):
        return [self.createRandomBook() for _ in range(count)]

    def insertBooks(self, books_list):
        self.db.session.add_all(books_list)
        self.db.session.commit()

    def deleteAllBooks(self):
        self.db.session.query(Book).delete()
        self.db.session.commit()

# @TODO: Write at least two tests for each endpoint - one each for success and error behavior.
#        You can feel free to write additional tests for nuanced functionality,
#        Such as adding a book without a rating, etc. 
#        Since there are four routes currently, you should have at least eight tests. 
# Optional: Update the book information in setUp to make the test database your own! 
    def test_fetch_all_books(self):
        res = self.client().get('/books')
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['total_books'], BOOKS_COUNT)
        self.assertEqual(len(data['books']), BOOKS_PER_SHELF)
    
    def test_fetch_all_books_page2(self):
        res = self.client().get('/books?page=2')
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(data['books']), 2)

    def test_fetch_all_books_inexistant_page(self):
        res = self.client().get('/books?page=2000')
        self.assertEqual(res.status_code, 404)

    def test_fetch_single_book(self):
        book = Book.query.first()
        res = self.client().get(f'/books/{book.id}')
        self.assertEqual(res.status_code, 200, f'Error fetching: /books/{book.id}\nFirst book id: {book.format()}')
    
    def test_fetch_single_inexistant_book(self):
        book = Book.query.order_by(Book.id).first()
        book_id = book.id - 1
        res = self.client().get(f'/books/{book_id}')
        self.assertEqual(res.status_code, 404)

    def test_update_first_book(self):
        book = Book.query.first()
        old_book = book.format()
        new_rating = book.rating % 5 + 1
        res = self.client().patch(f'/books/{book.id}', json={'rating': new_rating})
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        res = self.client().get(f"/books/{old_book['id']}")
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['book']['rating'], new_rating)

    def test_update_inexistant_book(self):
        book = Book.query.order_by(Book.id).first()
        book_id = book.id - 1
        res = self.client().patch(f'/books/{book_id}')
        self.assertEqual(res.status_code, 404)
    
    def test_update_book_invalid_rating(self):
        book = Book.query.first()
        new_rating = "I love GOD!"
        res = self.client().patch(f'/books/{book.id}', json={'rating': new_rating})
        data = res.get_json()
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)

    def test_delete_book(self):
        book = Book.query.order_by(Book.id).first()
        del_book = book.format()
        res = self.client().delete(f'/books/{book.id}')
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['deleted'], del_book['id'])
        self.assertEqual(data['total_books'], BOOKS_COUNT - 1)

        res = self.client().get(f"/books/{del_book['id']}")
        self.assertEqual(res.status_code, 404)

    def test_insert_new_book(self):
        res = self.client().post(f"/books", json=self.new_book)
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertNotEqual(data['created'], 0)
        self.assertEqual(data['total_books'], BOOKS_COUNT + 1)

    def test_insert_invalid_book(self):
        res = self.client().post(f"/books/1", json=self.new_book)
        self.assertEqual(res.status_code, 405)

    def test_search_book(self):
        books = Book.query.filter(Book.title.ilike('%python%')).all()
        books = [book.format() for book in books]
        res = self.client().get('/books/search', json={'search_term': 'python'})
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['books']), len(books))

    def test_search_inexistant_book(self):
        res = self.client().get('/books/search', json={'search_term': 'Tunisia'})
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(data['books']), 0)

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
