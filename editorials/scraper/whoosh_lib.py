import os
from django.db.models import signals
from django.conf import settings
from whoosh import fields, index
from app.models import Book, Category, Collection, Rating, Comment, ProfilePicture

BOOK_SCHEMA = fields.Schema(title=fields.TEXT,
                              description=fields.TEXT,
                              author=fields.TEXT,
                              collection=fields.TEXT,
                              editorial=fields.TEXT,
                              categories= fields.KEYWORD,
                              id=fields.ID(stored=True, unique=True))

COMMENT_SCHEMA = fields.Schema(text=fields.TEXT, id=fields.ID(stored=True, unique=True))

def create_index(sender=None, **kwargs):
    if not os.path.exists(settings.WHOOSH_INDEX_BOOK):
        os.makedirs(settings.WHOOSH_INDEX_BOOK, exist_ok=True)
        ix = index.create_in(settings.WHOOSH_INDEX_BOOK, schema=BOOK_SCHEMA)
    if not os.path.exists(settings.WHOOSH_INDEX_COMMENT):
        os.makedirs(settings.WHOOSH_INDEX_COMMENT, exist_ok=True)
        ix = index.create_in(settings.WHOOSH_INDEX_COMMENT, schema=COMMENT_SCHEMA)

signals.post_migrate.connect(create_index)

def new_book(sender, instance, created, **kwargs):
    ix = index.open_dir(settings.WHOOSH_INDEX_BOOK, schema=BOOK_SCHEMA)
    writer = ix.writer()
    
    categories = ""
    for category in instance.categories.all():
        if category == instance.categories.last():
            categories += category.name
        else:
            categories += category.name + " "
    
    collection = ""
    if instance.collection:
        collection = instance.collection.name
        
    if created:
        writer.add_document(title=instance.title, description=instance.description,
                            collection=collection, author=instance.author,
                            categories=categories, editorial=instance.editorial, id=str(instance.id))
    else:
        writer.update_document(title=instance.title, description=instance.description,
                            collection=collection, author=instance.author,
                            categories=categories, editorial=instance.editorial, id=str(instance.id))
    writer.commit()

signals.post_save.connect(new_book, sender=Book)

def new_comment(sender, instance, created, **kwargs):
    ix = index.open_dir(settings.WHOOSH_INDEX_COMMENT, schema=COMMENT_SCHEMA)
    writer = ix.writer()

    if created:
        writer.add_document(text=instance.text, id=str(instance.id))
    else:
        writer.update_document(text=instance.text, id=str(instance.id))
    
    writer.commit()

signals.post_save.connect(new_comment, sender=Comment)