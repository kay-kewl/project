import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Id(SqlAlchemyBase):
    __tablename__ = 'ids'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    tg_id = sqlalchemy.Column(sqlalchemy.Integer, unique=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User')



