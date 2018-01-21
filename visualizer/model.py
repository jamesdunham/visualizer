import logging

import os
from sqlalchemy import (Boolean, Column, Date, DateTime, Integer, String, create_engine, Binary, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

Base = declarative_base()

logging.info('Connecting to {}'.format(os.environ['PIPELINE_DB'].partition('?')[0]))
engine = create_engine(os.environ['PIPELINE_DB'], echo=False, connect_args={'connect_timeout': 5})
Session = sessionmaker(bind=engine)
session = Session()


class Document(Base):
    """A table for corpus documents.
    """
    __tablename__ = 'document'
    id = Column(Integer, primary_key=True)
    created_on = Column(DateTime)
    updated_on = Column(DateTime)
    # State of origin (e.g. 'california')
    state = Column(String)
    # Where the document was accessed/scraped
    url = Column(String, nullable=False)

    # Document contents exist as both HTML and extracted text, or just text (e.g. where extracted from PDFs,
    # or where a document represents an API request response)
    html = Column(String)
    text = Column(String)

    # The hash of the document contents (either HTML or text). Sometimes used for identification/deduplication
    md5 = Column(String(32))

    # A document can have many annotations
    annotations = relationship('Annotation', backref=backref('document',
                                                             cascade='all, delete-orphan',
                                                             single_parent=True),
                               cascade='all, delete-orphan', single_parent=True)
    # We re-annotate documents periodically (e.g. with an improved NER model)
    last_annotated = Column(DateTime, server_default=None)

    # If a document has been annotated manually, we call it a gold-parse document. Re-annotation will leave it
    # untouched.
    gold = Column(Boolean, default=False)

    # These columns give document metadata extracted from the text or collected from the document source.
    # Availability varies over states.
    bill_name = Column(String)
    chamber = Column(String)
    date = Column(Date)
    session = Column(String)
    topic = Column(String)

    # A serialized spacy.Doc instance. Inconsistently populated. Roughly doubles the size of the record,
    # and I've waffled on whether the storage or (re)compute expense is higher.
    doc = Column(Binary)

    # A document can refer to many bills (but in most states, just one)
    # bills = relationship("Bill", secondary='document_bill')

    # A document may contain references to many organizations. We annotate the document for these,
    # organizations = association_proxy('document_organizations', 'organization')


class Annotation(Base):
    """A table for document annotations.

    We load the annotation table by iterating over documents and applying a statistical or rule-based method for
    named entity recognition: in particular, identifying organizations.
    """
    __tablename__ = 'annotation'
    id = Column(Integer, primary_key=True)
    created_on = Column(DateTime)
    updated_on = Column(DateTime)

    # The annotated document text
    text = Column(String)

    # 'start' and 'end' are character offsets that slice the document text to give the annotation text
    start = Column(Integer)
    end = Column(Integer)

    # A document may contain many annotations, but an annotation exists only as a child of a single document.
    document_id = Column(Integer, ForeignKey('document.id', ondelete='CASCADE'), index=True)

    # E.g. 'Org' for an organization
    label = Column(String)

    # Same as document.state (e.g. 'california')
    state = Column(String)

    # If the annotation was manual we call it a gold parse, and automated re-annotation leaves it untouched.
    gold = Column(Boolean, default=False)

    # Organizations can be named (and those names annotated) in many documents. Annotations:organizations are many:one.
    organization_id = Column(Integer, ForeignKey('organization.id'))
