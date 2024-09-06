import dash
from dash import dcc, html
import pandas as pd
import sqlite3
from sqlalchemy import create_engine

# Create a connection to the SQLite database
conn = sqlite3.connect('example.db')

# Create a cursor object
cursor = conn.cursor()

# Create the users table
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  email TEXT,
                  join_date TEXT
              )''')

# Create the transactions table
cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                  transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,   

                  user_id INTEGER,
                  amount REAL,
                  transaction_date TEXT,
                  FOREIGN KEY (user_id) REFERENCES users(user_id)
              )''')

# Commit the changes
conn.commit()

# Insert sample data into the tables
cursor.execute("INSERT INTO users (name, email, join_date) VALUES ('Alice', 'alice@example.com', '2023-01-01')")
# ... (add more sample data)

conn.commit()

engine = create_engine('sqlite:///example.db')

# Task 1: Query users who joined within a specific date range
query1 = "SELECT * FROM users WHERE join_date BETWEEN '2023-01-01' AND '2023-12-31'"
users_in_range = pd.read_sql_query(query1, engine)

# Task 2: Calculate total amount spent by each user
query2 = "SELECT user_id, SUM(amount) AS total_spent FROM transactions GROUP BY user_id"
total_spent = pd.read_sql_query(query2, engine)

# Task 3: Generate a report showing each user's name, email, and total amount spent
query3 = "SELECT u.name, u.email, t.total_spent FROM users u JOIN total_spent t ON u.user_id = t.user_id"
user_report = pd.read_sql_query(query3, engine)

# Task 4: Find the top 3 users who spent the most
top_spenders = user_report.nlargest(3, 'total_spent')

# Task 5: Calculate the average transaction amount across all users
average_transaction_amount = total_spent['total_spent'].mean()

# Task 6: Identify users with no transactions
users_with_no_transactions = user_report[user_report['total_spent'] == 0]

from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

app = Dash(__name__)

@app.layout
def layout():
    return html.Div([
        html.H1("User Transactions Dashboard"),
        dcc.Graph(id='top-users-chart'),
        dcc.Graph(id='transactions-over-time'),
        html.Div(id='user-report-table'),
        html.Div(id='no-transactions-table')
    ])

if __name__ == '__main__':
    app.run_server(debug=True)

@app.callback(
    Output('top-users-chart', 'figure'),
    Output('transactions-over-time', 'figure'),
    Output('user-report-table', 'children'),
    Output('no-transactions-table', 'children')
)
def update_graphs():
    top_users = get_top_users()
    total_spent = [user[1] for user in top_users]
    user_names = [user[0] for user in top_users]

    # Bar chart for top users
    bar_fig = px.bar(x=user_names, y=total_spent, labels={'x': 'Users', 'y': 'Total Spent'})

    # Line chart for transaction amounts over time
    transactions_df = pd.read_sql('SELECT transaction_date, SUM(amount) as total FROM transactions GROUP BY transaction_date', engine)
    line_fig = px.line(transactions_df, x='transaction_date', y='total', title='Transaction Amounts Over Time')

    # User report table
    user_report = get_user_report()
    user_report_table = html.Table([
        html.Tr([html.Th("Name"), html.Th("Email"), html.Th("Total Spent")])] +
        [html.Tr([user[0], user[1], user[2]]) for user in user_report]
    ])

    # Users with no transactions table
    no_transactions = get_users_with_no_transactions()
    no_transactions_table = html.Table([
        html.Tr([html.Th("User ID"), html.Th("Name"), html.Th("Email"), html.Th("Join Date")])] +
        [html.Tr([user[0], user[1], user[2], user[3]]) for user in no_transactions]
    ])

    return bar_fig, line_fig, user_report_table, no_transactions_table


