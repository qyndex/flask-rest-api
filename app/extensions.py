"""Shared Flask extension instances.

Created without binding to an app so they can be used with the
application-factory pattern.
"""
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
