import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy #, or_
from flask_cors import CORS
import random

from models import setup_db, Book

BOOKS_PER_SHELF = 8


def paginate_books(request, selection):
    page = request.args.get('page', 1, type=int)
    start =  (page - 1) * BOOKS_PER_SHELF
    end = start + BOOKS_PER_SHELF

    books = [book.format() for book in selection]
    current_books = books[start:end]

    return current_books

def create_app(test_config=None):
  # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

  # CORS Headers 
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

  
    @app.route('/books')
    def retrieve_books():

        selection = Book.query.order_by(Book.id).all()
        current_books = paginate_books(request, selection)

        if len(current_books) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'books': current_books,
            'total_books': len(Book.query.all())
        })

    @app.route('/books/<int:book_id>')
    def retrieve_book(book_id):
        book = Book.query.get(book_id)

        if book is None:
            abort(404)

        return jsonify({
            'success': True,
            'book': book.format(),
            'total_books': len(Book.query.all())
        })

    @app.route('/books/<int:book_id>', methods=['PATCH'])
    def update_book(book_id):

        body = request.get_json()

        book = Book.query.filter(Book.id == book_id).one_or_none()
        if book is None:
            abort(404)

        try:
            if 'rating' in body:
                book.rating = int(body.get('rating'))
                book.update()
                return jsonify({
                    'success': True,
                })

        except:
            abort(400)

    @app.route('/books/<int:book_id>', methods=['DELETE'])
    def delete_book(book_id):
        book = Book.query.filter(Book.id == book_id).one_or_none()
        if book is None:
            abort(404)
        try:
            book.delete()
            selection = Book.query.order_by(Book.id).all()
            current_books = paginate_books(request, selection)

            return jsonify({
                'success': True,
                'deleted': book_id,
                'books': current_books,
                'total_books': len(Book.query.all())
            })
        except:
            abort(422)

    @app.route('/books', methods=['POST'])
    def create_book():
        body = request.get_json()

        new_title = body.get('title', None)
        new_author = body.get('author', None)
        new_rating = body.get('rating', None)

        try:
            book = Book(title=new_title, author=new_author, rating=new_rating)
            book.insert()

            selection = Book.query.order_by(Book.id).all()
            current_books = paginate_books(request, selection)
            # import pdb
            # pdb.set_trace()
            return jsonify({
                'success': True,
                'created': book.id,
                'books': current_books,
                'total_books': len(Book.query.all())
            })

        except:
            abort(422)
    
    @app.route('/books/search')
    def search_book_by_title():
        search_term = request.get_json().get('search_term', '')
        books = Book.query.filter(Book.title.ilike(f'%{search_term}%'))
        current_books = paginate_books(request, books)
        return jsonify({
            'success': True,
            'books': current_books,
            'total_books': len(Book.query.all())
        })


    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False, 
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(405)
    def not_found(error):
        return jsonify({
            "success": False, 
            "error": 405,
            "message": "Method Not Allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False, 
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False, 
            "error": 400,
            "message": "bad request"
        }), 400
  
    return app

