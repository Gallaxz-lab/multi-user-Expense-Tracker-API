from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from database.connection import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    owner = relationship("User", back_populates="categories")
    expenses = relationship("Expense", back_populates="category_rel", cascade="all, delete-orphan")
    
    __table_args__ = (UniqueConstraint('name', 'owner_id', name='_user_category_uc'),)

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False, server_default=func.current_date())
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    owner = relationship("User", back_populates="expenses")
    category_rel = relationship("Category", back_populates="expenses")
