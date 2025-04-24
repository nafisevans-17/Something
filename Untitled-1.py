
from flask import Flask, render_template, request, redirect, url_for
from decimal import Decimal
from datetime import datetime
import json
import os
from typing import List, Dict, Union

app = Flask(__name__)

class Transaction:
    def __init__(self, description: str, amount: Decimal, category: str = 'Other'):
        self.description = description
        self.amount = Decimal(str(amount))
        self.category = category
        self.date = datetime.now().strftime("%Y-%m-%d")

    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "amount": float(self.amount),
            "category": self.category,
            "date": self.date
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        return cls(
            description=data['description'],
            amount=Decimal(str(data['amount'])),
            category=data['category']
        )

class Income(Transaction):
    def __init__(self, description: str, amount: Decimal, category: str = 'Salary'):
        super().__init__(description, amount, category)

class Expense(Transaction):
    def __init__(self, description: str, amount: Decimal, category: str = 'Other'):
        super().__init__(description, amount, category)

class Budget:
    def __init__(self):
        self.income_categories = ['Salary', 'Investment', 'Business', 'Other']
        self.expense_categories = ['Food', 'Transportation', 'Housing', 'Entertainment', 'Other']
        self.filename = 'budget_data.json'
        self.incomes: List[Income] = []
        self.expenses: List[Expense] = []
        self.load_data()

    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                data = json.load(f)
                self.incomes = [Income.from_dict(item) for item in data.get('income', [])]
                self.expenses = [Expense.from_dict(item) for item in data.get('expenses', [])]

    def save_data(self):
        data = {
            'income': [income.to_dict() for income in self.incomes],
            'expenses': [expense.to_dict() for expense in self.expenses]
        }
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)

    def add_income(self, description: str, amount: Union[Decimal, str], category: str = 'Salary'):
        if not description or not amount:
            raise ValueError("Description and amount are required")
        try:
            income = Income(description, Decimal(amount), category)
            if income.amount <= 0:
                raise ValueError("Amount must be positive")
            self.incomes.append(income)
            self.save_data()
        except (ValueError, TypeError):
            raise ValueError("Invalid amount")

    def add_expense(self, description: str, amount: Union[Decimal, str], category: str = 'Other'):
        if not description or not amount:
            raise ValueError("Description and amount are required")
        try:
            expense = Expense(description, Decimal(amount), category)
            if expense.amount <= 0:
                raise ValueError("Amount must be positive")
            self.expenses.append(expense)
            self.save_data()
        except (ValueError, TypeError):
            raise ValueError("Invalid amount")

    def get_total_income(self) -> Decimal:
        return sum(income.amount for income in self.incomes)

    def get_total_expenses(self) -> Decimal:
        return sum(expense.amount for expense in self.expenses)

    def get_balance(self) -> Decimal:
        return self.get_total_income() - self.get_total_expenses()

    def get_expenses_by_category(self) -> Dict[str, Decimal]:
        category_totals = {category: Decimal('0') for category in self.expense_categories}
        for expense in self.expenses:
            category_totals[expense.category] += expense.amount
        return category_totals

    def get_monthly_summary(self) -> Dict[str, Decimal]:
        current_month = datetime.now().strftime("%Y-%m")
        monthly_income = sum(income.amount for income in self.incomes 
                           if income.date.startswith(current_month))
        monthly_expenses = sum(expense.amount for expense in self.expenses 
                             if expense.date.startswith(current_month))
        return {
            "income": monthly_income,
            "expenses": monthly_expenses,
            "balance": monthly_income - monthly_expenses
        }

budget = Budget()

@app.route('/')
def index():
    summary = {
        "total_income": float(budget.get_total_income()),
        "total_expenses": float(budget.get_total_expenses()),
        "balance": float(budget.get_balance()),
        "income": [income.to_dict() for income in budget.incomes],
        "expenses": [expense.to_dict() for expense in budget.expenses]
    }
    return render_template('index.html', summary=summary)

@app.route('/add_income', methods=['POST'])
def add_income():
    try:
        description = request.form['description'].strip()
        amount = request.form['amount']
        if not description or len(description) > 100:
            raise ValueError("Invalid description length")
        budget.add_income(description, amount)
        return redirect(url_for('index'))
    except ValueError as e:
        return str(e), 400

@app.route('/add_expense', methods=['POST'])
def add_expense():
    try:
        description = request.form['description'].strip()
        amount = request.form['amount']
        if not description or len(description) > 100:
            raise ValueError("Invalid description length")
        budget.add_expense(description, amount)
        return redirect(url_for('index'))
    except ValueError as e:
        return str(e), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
