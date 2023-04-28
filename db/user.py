import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    context_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    created = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    first_access = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    log_access = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    tg_id = orm.relationship('Id', back_populates='user')



