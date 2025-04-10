from flask import Flask, request, jsonify, render_template_string, g
import re
import sqlite3
import threading

app = Flask(__name__)
app.config['DATABASE'] = ':memory:'

# Database setup with thread-local storage
def get_db():
    if not hasattr(threading.current_thread(), 'db_conn'):
        threading.current_thread().db_conn = sqlite3.connect(app.config['DATABASE'])
        init_db(threading.current_thread().db_conn)
    return threading.current_thread().db_conn

def init_db(conn):
    cursor = conn.cursor()
    
    # Create sample tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        age INTEGER,
        department TEXT,
        salary REAL,
        join_date TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        amount INTEGER,
        order_date TEXT,
        status TEXT
    )
    """)
    
    # Clear existing data
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM orders")
    
    # Insert sample data
    users = [
        (1, 'John Doe', 'john@example.com', 28, 'Engineering', 75000, '2020-01-15'),
        (2, 'Jane Smith', 'jane@example.com', 32, 'Marketing', 65000, '2019-05-20'),
        (3, 'Mike Johnson', 'mike@example.com', 45, 'Engineering', 85000, '2018-03-10'),
        (4, 'Sarah Williams', 'sarah@example.com', 24, 'Sales', 55000, '2021-02-28'),
        (5, 'David Brown', 'david@example.com', 36, 'Engineering', 80000, '2019-11-05')
    ]
    
    orders = [
        (1, 1, 150, '2023-01-10', 'completed'),
        (2, 1, 230, '2023-02-15', 'completed'),
        (3, 2, 89, '2023-01-22', 'completed'),
        (4, 3, 450, '2023-03-05', 'pending'),
        (5, 5, 120, '2023-02-28', 'completed'),
        (6, 5, 75, '2023-03-10', 'completed'),
        (7, 5, 300, '2023-03-15', 'pending')
    ]
    
    cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", users)
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)
    
    conn.commit()

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>SNQL to SQL Converter</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary: #4361ee;
            --primary-light: #e6e9ff;
            --secondary: #3f37c9;
            --success: #4cc9f0;
            --danger: #f72585;
            --warning: #f8961e;
            --dark: #212529;
            --light: #f8f9fa;
            --gray: #6c757d;
            --gray-light: #e9ecef;
            --border-radius: 0.375rem;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            color: var(--dark);
            background-color: #f5f7fa;
            padding: 0;
            margin: 0;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            background-color: white;
            box-shadow: var(--shadow);
            padding: 1rem 0;
            margin-bottom: 2rem;
        }
        
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .logo i {
            font-size: 1.8rem;
        }
        
        .card {
            background-color: white;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            padding: 2rem;
            margin-bottom: 2rem;
        }
        
        h1, h2, h3 {
            color: var(--dark);
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        h1 {
            font-size: 2rem;
        }
        
        h2 {
            font-size: 1.5rem;
            border-bottom: 1px solid var(--gray-light);
            padding-bottom: 0.5rem;
        }
        
        h3 {
            font-size: 1.25rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        textarea, input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid var(--gray-light);
            border-radius: var(--border-radius);
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        
        textarea {
            min-height: 150px;
            resize: vertical;
        }
        
        textarea:focus, input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }
        
        button {
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: var(--border-radius);
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.1s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        button:hover {
            background-color: var(--secondary);
        }
        
        button:active {
            transform: translateY(1px);
        }
        
        button i {
            font-size: 1rem;
        }
        
        .result-container {
            margin-top: 2rem;
        }
        
        pre {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: var(--border-radius);
            border: 1px solid var(--gray-light);
            overflow-x: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        
        .tabs {
            display: flex;
            border-bottom: 1px solid var(--gray-light);
            margin-bottom: 1rem;
        }
        
        .tab {
            padding: 0.75rem 1.5rem;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            font-weight: 500;
            color: var(--gray);
            transition: all 0.2s;
        }
        
        .tab.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }
        
        .tab:hover:not(.active) {
            color: var(--dark);
            border-bottom-color: var(--gray-light);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1rem;
        }
        
        th, td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--gray-light);
        }
        
        th {
            background-color: var(--primary-light);
            font-weight: 600;
            color: var(--primary);
        }
        
        tr:hover {
            background-color: rgba(67, 97, 238, 0.05);
        }
        
        .examples {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .example-card {
            background-color: white;
            border-radius: var(--border-radius);
            padding: 1.5rem;
            box-shadow: var(--shadow);
            transition: transform 0.2s, box-shadow 0.2s;
            border-left: 4px solid var(--primary);
            cursor: pointer;
        }
        
        .example-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        
        .example-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--primary);
        }
        
        .example-desc {
            color: var(--gray);
            font-size: 0.9rem;
        }
        
        .suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .suggestion {
            background-color: var(--primary-light);
            color: var(--primary);
            padding: 0.25rem 0.5rem;
            border-radius: 1rem;
            font-size: 0.8rem;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .suggestion:hover {
            background-color: #d1d7ff;
        }
        
        .copy-btn {
            background-color: transparent;
            color: var(--gray);
            border: none;
            padding: 0.25rem 0.5rem;
            border-radius: var(--border-radius);
            cursor: pointer;
            font-size: 0.8rem;
            margin-left: 0.5rem;
            transition: color 0.2s;
        }
        
        .copy-btn:hover {
            color: var(--primary);
        }
        
        .alert {
            padding: 1rem;
            border-radius: var(--border-radius);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .alert-success {
            background-color: #e6f7ee;
            color: #0a7c4a;
            border-left: 4px solid #0a7c4a;
        }
        
        .alert-error {
            background-color: #fde8e8;
            color: #c81e1e;
            border-left: 4px solid #c81e1e;
        }
        
        .alert i {
            font-size: 1.25rem;
        }
        
        .flex {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .flex-between {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .mt-3 {
            margin-top: 1.5rem;
        }
        
        .mb-3 {
            margin-bottom: 1.5rem;
        }
        
        .text-muted {
            color: var(--gray);
        }
        
        .text-small {
            font-size: 0.875rem;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .header-content {
                padding: 0 1rem;
            }
            
            .examples {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <a href="/" class="logo">
                <i class="fas fa-exchange-alt"></i>
                <span>SNQL Converter</span>
            </a>
            <div class="text-muted text-small">
                Simple Natural Query Language to SQL
            </div>
        </div>
    </header>
    
    <div class="container">
        <div class="card">
            <h1>SNQL to SQL Converter</h1>
            <p class="text-muted">Convert natural language queries to SQL with ease</p>
            
            <form method="post">
                <div class="form-group">
                    <label for="snql">Enter your SNQL query:</label>
                    <textarea name="snql" id="snql" placeholder="Example: get name, email from users where age is greater than 25 order by name limit 5">{{ snql_input }}</textarea>
                    
                    <div class="suggestions">
                        <div class="suggestion" onclick="insertSuggestion('get name, email from users')">get name, email from users</div>
                        <div class="suggestion" onclick="insertSuggestion('get count of id from users where age is greater than 30')">count records</div>
                        <div class="suggestion" onclick="insertSuggestion('get users.name, orders.amount from users join orders on users.id = orders.user_id')">join tables</div>
                        <div class="suggestion" onclick="insertSuggestion('get avg of salary from users group by department')">aggregate functions</div>
                    </div>
                </div>
                
                <button type="submit">
                    <i class="fas fa-exchange-alt"></i>
                    Convert to SQL
                </button>
            </form>
        </div>
        
        {% if sql %}
        <div class="card result-container">
            <div class="flex-between">
                <h2>Conversion Results</h2>
                <button class="copy-btn" onclick="copyToClipboard('sql-output')">
                    <i class="far fa-copy"></i> Copy SQL
                </button>
            </div>
            
            <div class="tabs">
                <div class="tab active" onclick="switchTab('sql-tab')">SQL Query</div>
                <div class="tab" onclick="switchTab('results-tab')">Query Results</div>
                <div class="tab" onclick="switchTab('info-tab')">Query Info</div>
            </div>
            
            <div class="tab-content active" id="sql-tab">
                <pre id="sql-output">{{ sql }}</pre>
                
                {% if query_error %}
                <div class="alert alert-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <div>
                        <strong>SQL Error:</strong> {{ query_error }}
                    </div>
                </div>
                {% endif %}
            </div>
            
            <div class="tab-content" id="results-tab">
                {% if query_results %}
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                {% for col in query_columns %}
                                <th>{{ col }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in query_results %}
                            <tr>
                                {% for item in row %}
                                <td>{{ item if item is not none else 'NULL' }}</td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    <p class="text-muted text-small">Showing {{ query_results|length }} row{% if query_results|length != 1 %}s{% endif %}</p>
                </div>
                {% elif query_error %}
                <div class="alert alert-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <div>
                        <strong>Error executing query:</strong> {{ query_error }}
                    </div>
                </div>
                {% else %}
                <div class="alert">
                    <i class="fas fa-info-circle"></i>
                    No results to display
                </div>
                {% endif %}
            </div>
            
            <div class="tab-content" id="info-tab">
                <div class="mb-3">
                    <h3>Query Information</h3>
                    <p class="text-muted">Details about your converted query</p>
                </div>
                
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    <div>
                        <strong>Successfully converted</strong>
                        <p class="text-small">Your SNQL query was converted to valid SQL</p>
                    </div>
                </div>
                
                <div>
                    <h4>Query Summary</h4>
                    <ul style="list-style-type: none; padding-left: 0;">
                        <li class="mb-2"><strong>Tables:</strong> {{ ', '.join(query_tables) if query_tables else 'None detected' }}</li>
                        <li class="mb-2"><strong>Columns Selected:</strong> {{ query_columns|length }}</li>
                        <li class="mb-2"><strong>Conditions:</strong> {{ 'Yes' if 'WHERE' in sql else 'No' }}</li>
                        <li class="mb-2"><strong>Joins:</strong> {{ 'Yes' if 'JOIN' in sql else 'No' }}</li>
                    </ul>
                </div>
            </div>
        </div>
        {% endif %}
        
        <div class="card">
            <h2>Example Queries</h2>
            <p class="text-muted">Try these example SNQL queries to get started</p>
            
            <div class="examples">
                <div class="example-card" onclick="insertSuggestion('get name, email from users where age is greater than 25 order by name limit 5')">
                    <div class="example-title">Basic Query</div>
                    <div class="example-desc">Get specific columns with a simple condition</div>
                </div>
                
                <div class="example-card" onclick="insertSuggestion('get users.name, orders.amount from users join orders on users.id = orders.user_id where orders.amount is greater than 100')">
                    <div class="example-title">Table Join</div>
                    <div class="example-desc">Combine data from multiple tables</div>
                </div>
                
                <div class="example-card" onclick="insertSuggestion('get count of id, avg of salary from users where department is equal to "Engineering" group by department')">
                    <div class="example-title">Aggregation</div>
                    <div class="example-desc">Use count, avg and group by</div>
                </div>
                
                <div class="example-card" onclick="insertSuggestion('get users.name, sum of orders.amount from users left join orders on users.id = orders.user_id group by users.id order by sum of orders.amount desc limit 3')">
                    <div class="example-title">Advanced Query</div>
                    <div class="example-desc">Join, aggregate, sort and limit</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function insertSuggestion(text) {
            const textarea = document.getElementById('snql');
            textarea.value = text;
            textarea.focus();
        }
        
        function switchTab(tabId) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Deactivate all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Activate selected tab
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }
        
        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.textContent || element.innerText;
            
            navigator.clipboard.writeText(text).then(() => {
                const btn = event.currentTarget;
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                
                setTimeout(() => {
                    btn.innerHTML = '<i class="far fa-copy"></i> Copy SQL';
                }, 2000);
            });
        }
    </script>
</body>
</html>
"""

def snql_to_sql(snql: str) -> str:
    snql = snql.strip()
    
    # Extract basic query components
    match = re.search(r'get (.+?) from (\w+)', snql, re.IGNORECASE)
    if not match:
        return "Invalid SNQL syntax"

    # Process fields, handle aggregate functions
    raw_fields = match.group(1)
    fields = []
    aggregates = ["count", "sum", "avg", "max", "min"]
    
    # Check for aggregate functions
    for field in raw_fields.split(','):
        field = field.strip()
        for agg in aggregates:
            if field.lower().startswith(f"{agg} of "):
                field_name = field[len(f"{agg} of "):].strip()
                fields.append(f"{agg.upper()}({field_name})")
                break
        else:
            fields.append(field)
    
    fields_str = ", ".join(fields)
    table = match.group(2)
    
    # Handle JOINs
    join_clause = ""
    join_types = ["join", "left join", "right join", "inner join", "outer join"]
    
    for join_type in join_types:
        join_pattern = rf'{join_type} (\w+) on (.+?)(?=\s+(?:{"|".join(join_types)})|where|group by|order by|limit|$)'
        join_matches = re.finditer(join_pattern, snql, re.IGNORECASE)
        
        for join_match in join_matches:
            join_table = join_match.group(1)
            join_condition = join_match.group(2).strip()
            join_clause += f" {join_type.upper()} {join_table} ON {join_condition}"
    
    # Process WHERE clause
    where_clause = ""
    where_match = re.search(r'where (.+?)(?=\s+group by|order by|limit|$|\s*$)', snql, re.IGNORECASE)
    if where_match:
        condition = where_match.group(1).strip()
        # Enhanced condition parsing
        condition = re.sub(r'(\w+)\s+is\s+greater\s+than\s+(\d+|"\w+"|\'\w+\')', r'\1 > \2', condition, flags=re.IGNORECASE)
        condition = re.sub(r'(\w+)\s+is\s+less\s+than\s+(\d+|"\w+"|\'\w+\')', r'\1 < \2', condition, flags=re.IGNORECASE)
        condition = re.sub(r'(\w+)\s+is\s+equal\s+to\s+(\d+|"\w+"|\'\w+\')', r'\1 = \2', condition, flags=re.IGNORECASE)
        condition = re.sub(r'(\w+)\s+is\s+not\s+equal\s+to\s+(\d+|"\w+"|\'\w+\')', r'\1 != \2', condition, flags=re.IGNORECASE)
        condition = re.sub(r'(\w+)\s+is\s+null', r'\1 IS NULL', condition, flags=re.IGNORECASE)
        condition = re.sub(r'(\w+)\s+is\s+not\s+null', r'\1 IS NOT NULL', condition, flags=re.IGNORECASE)
        condition = re.sub(r'(\w+)\s+like\s+"(.+?)"', r"\1 LIKE '\2'", condition, flags=re.IGNORECASE)
        condition = re.sub(r'(\w+)\s+between\s+(\d+|"\w+"|\'\w+\')\s+and\s+(\d+|"\w+"|\'\w+\')', r'\1 BETWEEN \2 AND \3', condition, flags=re.IGNORECASE)
        condition = re.sub(r'\s+and\s+', ' AND ', condition, flags=re.IGNORECASE)
        condition = re.sub(r'\s+or\s+', ' OR ', condition, flags=re.IGNORECASE)
        condition = re.sub(r'\s+not\s+', ' NOT ', condition, flags=re.IGNORECASE)
        where_clause = f" WHERE {condition}"
    
    # Process GROUP BY clause
    group_by_clause = ""
    group_match = re.search(r'group by (.+?)(?=\s+order by|limit|$|\s*$)', snql, re.IGNORECASE)
    if group_match:
        group_fields = group_match.group(1).strip()
        group_by_clause = f" GROUP BY {group_fields}"
    
    # Process HAVING clause
    having_clause = ""
    having_match = re.search(r'having (.+?)(?=\s+order by|limit|$|\s*$)', snql, re.IGNORECASE)
    if having_match:
        having_condition = having_match.group(1).strip()
        having_condition = re.sub(r'(\w+)\s+is\s+greater\s+than\s+(\d+)', r'\1 > \2', having_condition, flags=re.IGNORECASE)
        having_condition = re.sub(r'(\w+)\s+is\s+less\s+than\s+(\d+)', r'\1 < \2', having_condition, flags=re.IGNORECASE)
        having_clause = f" HAVING {having_condition}"
    
    # Process ORDER BY clause
    order_by_clause = ""
    order_match = re.search(r'order by (.+?)(?=\s+limit|$|\s*$)', snql, re.IGNORECASE)
    if order_match:
        order_fields = order_match.group(1).strip()
        
        # Handle special ordering syntax
        for agg in aggregates:
            pattern = rf"{agg}\s+of\s+(\w+[\.\w+]*)"
            order_fields = re.sub(pattern, f"{agg.upper()}(\\1)", order_fields, flags=re.IGNORECASE)
        
        order_direction = "ASC"
        if " desc" in order_fields.lower():
            order_fields = order_fields.lower().replace(" desc", "")
            order_direction = "DESC"
        elif " asc" in order_fields.lower():
            order_fields = order_fields.lower().replace(" asc", "")
        
        order_by_clause = f" ORDER BY {order_fields} {order_direction}"
    
    # Process LIMIT clause
    limit_clause = ""
    limit_match = re.search(r'limit (\d+)', snql, re.IGNORECASE)
    if limit_match:
        limit = limit_match.group(1)
        limit_clause = f" LIMIT {limit}"
    
    # Construct the SQL query
    sql = f"SELECT {fields_str} FROM {table}{join_clause}{where_clause}{group_by_clause}{having_clause}{order_by_clause}{limit_clause};"
    
    return sql

def extract_tables_from_sql(sql: str) -> list:
    # Extract tables from FROM and JOIN clauses
    from_matches = re.findall(r'FROM\s+(\w+)', sql, re.IGNORECASE)
    join_matches = re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
    return list(set(from_matches + join_matches))

@app.route('/', methods=['GET', 'POST'])
def index():
    sql = None
    snql_input = ""
    query_results = None
    query_columns = []
    query_error = None
    query_tables = []
    
    if request.method == 'POST':
        snql_input = request.form['snql']
        sql = snql_to_sql(snql_input)
        
        # Execute the SQL query against our sample database
        if sql and not sql.startswith("Invalid SNQL syntax"):
            try:
                db = get_db()
                cursor = db.cursor()
                cursor.execute(sql)
                
                # Get column names
                query_columns = [description[0] for description in cursor.description]
                query_results = cursor.fetchall()
                
                # Extract tables from SQL
                query_tables = extract_tables_from_sql(sql)
                
            except sqlite3.Error as e:
                query_error = str(e)
    
    return render_template_string(
        HTML_TEMPLATE,
        sql=sql,
        snql_input=snql_input,
        query_results=query_results,
        query_columns=query_columns,
        query_error=query_error,
        query_tables=query_tables
    )

@app.teardown_appcontext
def close_db(error):
    if hasattr(threading.current_thread(), 'db_conn'):
        threading.current_thread().db_conn.close()
        del threading.current_thread().db_conn

if __name__ == '__main__':
    # Initialize the database for the main thread
    with app.app_context():
        get_db()
    app.run(debug=True)