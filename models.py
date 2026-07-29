from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key= True, index= True)
    name = Column(String, nullable= False, unique= True)
    expenses = relationship("Expense", back_populates="category_rel")
    
    
class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False, server_default=func.current_date())
    category_rel = relationship("Category", back_populates="expenses")