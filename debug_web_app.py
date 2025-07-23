# debug_web_app.py
from flask import Flask, render_template, jsonify
import sqlite3
import pandas as pd
from datetime import datetime
import traceback

app = Flask(__name__)

class LSCWebApp:
    def __init__(self, db_path='lsc_database.db'):
        self.db_path = db_path
    
    def query_database(self, query):
        """Execute a query and return results"""
        try:
            print(f"🔍 Executing query: {query}")
            conn = sqlite3.connect(self.db_path)
            result = pd.read_sql_query(query, conn)
            conn.close()
            print(f"✅ Query successful, {len(result)} rows returned")
            return result.to_dict('records')
        except Exception as e:
            print(f"❌ Database error: {e}")
            traceback.print_exc()
            return []

# Initialize the web app
lsc_web = LSCWebApp()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/test')
def test_connection():
    """Test endpoint to check database connection"""
    try:
        conn = sqlite3.connect(lsc_web.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Database connected successfully',
            'tables': [table[0] for table in tables]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/team-summary')
def team_summary():
    """Get team performance summary"""
    try:
        print("🏆 Getting team summary...")
        
        # First, let's see what tables we have
        conn = sqlite3.connect(lsc_web.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Available tables: {tables}")
        
        # Try to find a match results table
        match_table = None
        for table in tables:
            if 'match' in table.lower():
                match_table = table
                break
        
        if not match_table:
            return jsonify({'error': 'No match results table found', 'tables': tables})
        
        print(f"Using table: {match_table}")
        
        # Get column names
        cursor.execute(f"PRAGMA table_info([{match_table}])")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Available columns: {columns}")
        
        # Try a simple query first
        cursor.execute(f"SELECT * FROM [{match_table}] LIMIT 5")
        sample_data = cursor.fetchall()
        print(f"Sample data: {sample_data}")
        
        conn.close()
        
        # Now, actually compute stats from the match table
        # Fetch all rows
        conn = sqlite3.connect(lsc_web.db_path)
        df = pd.read_sql_query(f"SELECT * FROM [{match_table}] WHERE Result IS NOT NULL", conn)
        conn.close()

        total_matches = len(df)
        wins = len(df[df['Result'] == 'W'])
        draws = len(df[df['Result'] == 'D'])
        losses = len(df[df['Result'] == 'L'])
        goals_for = df['GF'].sum() if 'GF' in df.columns else 0
        goals_against = df['GA'].sum() if 'GA' in df.columns else 0

        return jsonify({
            'table_used': match_table,
            'columns': columns,
            'total_matches': int(total_matches),
            'wins': int(wins),
            'draws': int(draws),
            'losses': int(losses),
            'goals_for': float(goals_for),
            'goals_against': float(goals_against)
        })
        
    except Exception as e:
        print(f"❌ Error in team_summary: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)})

@app.route('/api/recent-matches')
def recent_matches():
    """Get recent match results"""
    try:
        print("⚽ Getting recent matches...")
        
        conn = sqlite3.connect(lsc_web.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Find match table
        match_table = None
        for table in tables:
            if 'match' in table.lower():
                match_table = table
                break
        
        if not match_table:
            return jsonify([])
        
        # Get all data from match table
        cursor.execute(f"SELECT * FROM [{match_table}] LIMIT 10")
        data = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info([{match_table}])")
        columns = [col[1] for col in cursor.fetchall()]
        
        conn.close()
        
        # Convert to list of dictionaries
        results = []
        for row in data:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i] if i < len(row) else None
            results.append(row_dict)
        
        print(f"Found {len(results)} matches")
        return jsonify(results)
        
    except Exception as e:
        print(f"❌ Error in recent_matches: {e}")
        traceback.print_exc()
        return jsonify([])

@app.route('/api/player-stats')
def player_stats():
    """Get player performance stats"""
    try:
        print("👥 Getting player stats...")
        
        conn = sqlite3.connect(lsc_web.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Find player table
        player_table = None
        for table in tables:
            if 'player' in table.lower():
                player_table = table
                break
        
        if not player_table:
            return jsonify({'error': 'No player table found', 'tables': tables})
        
        # Get sample data
        cursor.execute(f"SELECT * FROM [{player_table}] LIMIT 10")
        data = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info([{player_table}])")
        columns = [col[1] for col in cursor.fetchall()]
        
        conn.close()
        
        # Convert to list of dictionaries
        results = []
        for row in data:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i] if i < len(row) else None
            results.append(row_dict)
        
        return jsonify({'table': player_table, 'columns': columns, 'data': results})
        
    except Exception as e:
        print(f"❌ Error in player_stats: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)})

@app.route('/api/database-info')
def database_info():
    """Get information about database tables"""
    try:
        print("🗄️ Getting database info...")
        
        conn = sqlite3.connect(lsc_web.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        table_info = []
        for table_tuple in tables:
            table_name = table_tuple[0]
            if not table_name.startswith('sqlite_'):
                cursor.execute(f"SELECT COUNT(*) as count FROM [{table_name}]")
                count = cursor.fetchone()[0]
                table_info.append({
                    'name': table_name,
                    'rows': count
                })
        
        conn.close()
        print(f"Found {len(table_info)} tables")
        return jsonify(table_info)
        
    except Exception as e:
        print(f"❌ Error in database_info: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("🚀 Starting debug Flask app...")
    print("Visit http://127.0.0.1:5000/api/test to test database connection")
    app.run(debug=True, port=5000)