from sqlalchemy import Column, Integer, String, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    artikul = Column(Integer, unique=True, nullable=False)
    price = Column(Float, nullable=False)
    rating = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)