import os
from flask import Flask
from flask_graphql import GraphQLView
import graphene
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Initialize Flask app
app = Flask(__name__)

# Setup database
database_url = os.environ.get('DATABASE_URL', 'postgresql://bookuser:bookpass@localhost/bookdb')
engine = create_engine(database_url)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Base Query class and decorator
class BaseQuery(graphene.ObjectType):
    pass

query_classes = []

def register_query(cls):
    query_classes.append(cls)
    return cls

# Base Model
class BaseModel(Base):
    __abstract__ = True
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Book Model and Type
class BookModel(BaseModel):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    published_year = Column(Integer)

class Book(graphene.ObjectType):
    id = graphene.Int()
    title = graphene.String()
    author = graphene.String()
    published_year = graphene.Int()

# Author Model and Type
class AuthorModel(BaseModel):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = graphene.String()
    birth_year = graphene.Int()

class Author(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    birth_year = graphene.Int()

Base.metadata.create_all(engine)

# Book Query
@register_query
class BookQuery(BaseQuery):
    books = graphene.List(Book)
    book = graphene.Field(Book, id=graphene.Int())

    def resolve_books(self, info):
        session = Session()
        books = session.query(BookModel).all()
        return [Book(**book.to_dict()) for book in books]

    def resolve_book(self, info, id):
        session = Session()
        book = session.query(BookModel).filter(BookModel.id == id).first()
        return Book(**book.to_dict()) if book else None

# Author Query
@register_query
class AuthorQuery(BaseQuery):
    authors = graphene.List(Author)
    author = graphene.Field(Author, id=graphene.Int())

    def resolve_authors(self, info):
        session = Session()
        authors = session.query(AuthorModel).all()
        return [Author(**author.to_dict()) for author in authors]

    def resolve_author(self, info, id):
        session = Session()
        author = session.query(AuthorModel).filter(AuthorModel.id == id).first()
        return Author(**author.to_dict()) if author else None

# Combine all queries
class Query(*query_classes, BaseQuery):
    pass

# Mutations
class CreateBook(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        author = graphene.String(required=True)
        published_year = graphene.Int(required=True)

    book = graphene.Field(Book)

    def mutate(self, info, title, author, published_year):
        session = Session()
        new_book = BookModel(title=title, author=author, published_year=published_year)
        session.add(new_book)
        session.commit()
        return CreateBook(book=Book(**new_book.to_dict()))

class CreateAuthor(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        birth_year = graphene.Int(required=True)

    author = graphene.Field(Author)

    def mutate(self, info, name, birth_year):
        session = Session()
        new_author = AuthorModel(name=name, birth_year=birth_year)
        session.add(new_author)
        session.commit()
        return CreateAuthor(author=Author(**new_author.to_dict()))

class Mutation(graphene.ObjectType):
    create_book = CreateBook.Field()
    create_author = CreateAuthor.Field()

# Create schema
schema = graphene.Schema(query=Query, mutation=Mutation)

# Add GraphQL view to Flask app
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)