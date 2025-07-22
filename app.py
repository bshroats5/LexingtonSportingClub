# web_app.py
from flask import Flask, render_template, jsonify
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)

class LSCWebApp:
    def __init__(self, db_path='lsc_database.db'):
        self.db_path = db_path
    
    def query_database(self, query):
        """Execute a query and return results"""
        try:
            conn = sqlite3.connect(self.db_path)
            result = pd.read_sql_query(query, conn)
            conn.close()
            return result.to_dict('records')
        except Exception as e:
            print(f"Database error: {e}")
            return []

# Initialize the web app
lsc_web = LSCWebApp()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/team-summary')
def team_summary():
    """Get team performance summary"""
    try:
        query = """
            SELECT 
                COUNT(*) as total_matches,
                SUM(CASE WHEN Result = 'W' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN Result = 'D' THEN 1 ELSE 0 END) as draws,
                SUM(CASE WHEN Result = 'L' THEN 1 ELSE 0 END) as losses,
                SUM(GF) as goals_for,
                SUM(GA) as goals_against
            FROM match_results 
            WHERE Result IS NOT NULL
        """
        result = lsc_web.query_database(query)
        return jsonify(result[0] if result else {})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/recent-matches')
def recent_matches():
    """Get recent match results"""
    query = """
        SELECT 
            Date,
            Opponent,
            Venue,
            Result,
            GF as goals_for,
            GA as goals_against,
            Attendance
        FROM match_results 
        WHERE Date IS NOT NULL AND Result IS NOT NULL
        ORDER BY Date DESC 
        LIMIT 10
    """
    results = lsc_web.query_database(query)
    return jsonify(results)

@app.route('/api/player-stats')
def player_stats():
    """Get player performance stats"""
    try:
        # Try different possible table structures
        tables = ['player_performance', 'player_stats_1', 'player_standard_stats']
        
        for table in tables:
            try:
                query = f"""
                    SELECT * FROM {table} 
                    WHERE "Unnamed_0_level_0_Player" NOT IN ('Squad Total', 'Opponent Total')
                    AND "Unnamed_0_level_0_Player" IS NOT NULL
                    LIMIT 15
                """
                results = lsc_web.query_database(query)
                if results:
                    return jsonify({'table': table, 'data': results})
            except:
                continue
        
        return jsonify({'error': 'No player stats found'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/database-info')
def database_info():
    """Get information about database tables"""
    try:
        conn = sqlite3.connect(lsc_web.db_path)
        tables_query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        tables = pd.read_sql_query(tables_query, conn)
        
        table_info = []
        for table_name in tables['name']:
            if not table_name.startswith('sqlite_'):
                count_query = f"SELECT COUNT(*) as count FROM [{table_name}]"
                count = pd.read_sql_query(count_query, conn)['count'][0]
                table_info.append({
                    'name': table_name,
                    'rows': count
                })
        
        conn.close()
        return jsonify(table_info)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)