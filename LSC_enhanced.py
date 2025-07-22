# Enhanced LSC Database Management System
# libraries
import pandas as pd
import sqlite3
from datetime import datetime, date
import os

# fbref table link
url_df = 'https://fbref.com/en/squads/7622315f/Lexington-SC-Stats'

class LSCDatabaseManager:
    """Comprehensive LSC Stats Database Manager"""
    
    def __init__(self, db_path='lsc_database.db'):
        self.db_path = db_path
        self.url = url_df
        
    def create_database(self):
        """Create and populate LSC database with all stats"""
        
        # Create database connection
        conn = sqlite3.connect(self.db_path)
        
        print("🔄 Fetching data from FBRef...")
        # Get all tables from the webpage
        tables = pd.read_html(self.url)
        
        print(f"📊 Found {len(tables)} tables on the page")
        
        # Process each table and save to database
        table_names = []
        
        for i, table in enumerate(tables):
            # Clean column names for multi-index tables
            if hasattr(table.columns, 'nlevels') and table.columns.nlevels > 1:
                table.columns = [' '.join(col).strip() for col in table.columns]
            
            # Reset index
            table = table.reset_index(drop=True)
            
            # Determine table type based on content
            table_name = self._determine_table_type(table, i)
            table_names.append(table_name)
            
            # Clean and save table to database
            clean_table = self._clean_dataframe(table)
            clean_table.to_sql(table_name, conn, if_exists='replace', index=False)
            
            print(f"✅ Saved table {i+1}: {table_name} ({len(clean_table)} rows, {len(clean_table.columns)} columns)")
        
        # Create metadata table
        self._create_metadata_table(conn, table_names)
        
        # Create additional views for easier querying
        self._create_database_views(conn)
        
        conn.close()
        print(f"\n🎉 Database created successfully: {self.db_path}")
        return self.db_path
        
    def _determine_table_type(self, df, table_index):
        """Determine what type of table this is based on content"""
        
        # Check column names to identify table type
        columns = [str(col).lower() for col in df.columns]
        
        if any('player' in col for col in columns):
            if any('save' in col or 'gk' in col or 'goalkeeper' in col for col in columns):
                return 'goalkeeper_stats'
            elif any('disciplinary' in col or 'crdy' in col or 'crdr' in col for col in columns):
                return 'player_disciplinary'
            elif any('xg' in col or 'expected' in col for col in columns):
                return 'player_advanced_stats'
            elif any('performance' in col or '90s' in col for col in columns):
                return 'player_performance'
            else:
                return f'player_stats_{table_index + 1}'
        
        elif any('date' in col or 'comp' in col or 'opponent' in col for col in columns):
            return 'match_results'
        
        elif any('squad' in col or 'team' in col for col in columns):
            if any('home' in col and 'away' in col for col in columns):
                return 'league_table_detailed'
            else:
                return 'league_table'
        
        else:
            return f'data_table_{table_index + 1}'

    def _clean_dataframe(self, df):
        """Clean dataframe for database storage"""
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Replace NaN with None for better SQLite compatibility
        df = df.where(pd.notnull(df), None)
        
        # Clean column names - remove special characters and make them database-friendly
        df.columns = [
            col.replace('/', '_')
            .replace(' ', '_')
            .replace('-', '_')
            .replace('+', '_plus_')
            .replace('%', '_pct')
            .replace('(', '_')
            .replace(')', '_')
            .replace(':', '_')
            .strip('_')
            for col in df.columns
        ]
        
        return df

    def _create_metadata_table(self, conn, table_names):
        """Create a metadata table with information about the database"""
        metadata = pd.DataFrame({
            'table_name': table_names,
            'created_date': [datetime.now().isoformat()] * len(table_names),
            'source_url': [self.url] * len(table_names),
            'last_updated': [datetime.now().isoformat()] * len(table_names)
        })
        metadata.to_sql('database_metadata', conn, if_exists='replace', index=False)

    def _create_database_views(self, conn):
        """Create SQL views for easier data access"""
        
        # Create a view for active players (non-totals)
        try:
            conn.execute("""
                CREATE VIEW IF NOT EXISTS active_players AS
                SELECT * FROM player_performance 
                WHERE "Unnamed_0_level_0_Player" NOT IN ('Squad Total', 'Opponent Total')
                AND "Unnamed_0_level_0_Player" IS NOT NULL
            """)
            
            # Create a view for completed matches
            conn.execute("""
                CREATE VIEW IF NOT EXISTS completed_matches AS
                SELECT * FROM match_results 
                WHERE Result IS NOT NULL 
                AND Date IS NOT NULL
                ORDER BY Date DESC
            """)
            
            conn.commit()
            print("✅ Created database views for easier querying")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not create views: {e}")

    def query_database(self, query):
        """Execute a query on the database"""
        conn = sqlite3.connect(self.db_path)
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result

    def get_database_info(self):
        """Get comprehensive information about all tables in the database"""
        conn = sqlite3.connect(self.db_path)
        
        # Get all table names
        tables_query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        tables = pd.read_sql_query(tables_query, conn)
        
        print("📊 LSC DATABASE OVERVIEW")
        print("=" * 60)
        
        for table_name in tables['name']:
            if table_name.startswith('sqlite_'):
                continue
                
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM [{table_name}]"
            count = pd.read_sql_query(count_query, conn)['count'][0]
            
            # Get column info
            columns_query = f"PRAGMA table_info([{table_name}])"
            columns = pd.read_sql_query(columns_query, conn)
            
            print(f"\n📋 {table_name.upper().replace('_', ' ')}:")
            print(f"   Rows: {count}")
            print(f"   Columns: {len(columns)}")
            if len(columns) <= 10:
                print(f"   Column names: {', '.join(columns['name'].tolist())}")
            else:
                print(f"   First 10 columns: {', '.join(columns['name'].tolist()[:10])}...")
        
        conn.close()

    def get_player_stats(self, limit=10):
        """Get top players by various metrics"""
        try:
            # Try to get player performance data
            query = """
                SELECT 
                    "Unnamed_0_level_0_Player" as Player,
                    "Unnamed_1_level_0_Nation" as Nation,
                    "Unnamed_2_level_0_Pos" as Position,
                    "Performance_CrdY" as Yellow_Cards,
                    "Performance_CrdR" as Red_Cards,
                    "Performance_Fls" as Fouls,
                    "Performance_Int" as Interceptions,
                    "Performance_TklW" as Tackles_Won
                FROM player_performance 
                WHERE Player NOT IN ('Squad Total', 'Opponent Total')
                AND Player IS NOT NULL
                ORDER BY Yellow_Cards DESC
                LIMIT ?
            """
            return self.query_database(query.replace('?', str(limit)))
        except Exception as e:
            print(f"Error getting player stats: {e}")
            return None

    def get_recent_matches(self, limit=10):
        """Get recent match results"""
        try:
            query = f"""
                SELECT 
                    Date,
                    Time,
                    Comp as Competition,
                    Venue,
                    Result,
                    GF as Goals_For,
                    GA as Goals_Against,
                    Opponent,
                    Attendance,
                    Captain
                FROM match_results 
                WHERE Date IS NOT NULL AND Result IS NOT NULL
                ORDER BY Date DESC 
                LIMIT {limit}
            """
            return self.query_database(query)
        except Exception as e:
            print(f"Error getting match results: {e}")
            return None

    def get_team_summary(self):
        """Get overall team performance summary"""
        try:
            matches = self.get_recent_matches(50)  # Get more matches for better stats
            if matches is not None and not matches.empty:
                total_matches = len(matches)
                wins = len(matches[matches['Result'] == 'W'])
                draws = len(matches[matches['Result'] == 'D'])
                losses = len(matches[matches['Result'] == 'L'])
                
                goals_for = matches['Goals_For'].sum()
                goals_against = matches['Goals_Against'].sum()
                
                print(f"\n🏆 LEXINGTON SC SEASON SUMMARY")
                print("=" * 40)
                print(f"Matches Played: {total_matches}")
                print(f"Wins: {wins} | Draws: {draws} | Losses: {losses}")
                print(f"Win Rate: {(wins/total_matches)*100:.1f}%")
                print(f"Goals Scored: {goals_for}")
                print(f"Goals Conceded: {goals_against}")
                print(f"Goal Difference: {goals_for - goals_against}")
                print(f"Goals per Match: {goals_for/total_matches:.2f}")
                
        except Exception as e:
            print(f"Error generating team summary: {e}")

    def export_data(self, table_name, format='csv'):
        """Export table data to CSV or Excel"""
        try:
            df = self.query_database(f"SELECT * FROM [{table_name}]")
            filename = f"lsc_{table_name}_{datetime.now().strftime('%Y%m%d')}"
            
            if format.lower() == 'csv':
                filepath = f"{filename}.csv"
                df.to_csv(filepath, index=False)
            elif format.lower() == 'excel':
                filepath = f"{filename}.xlsx"
                df.to_excel(filepath, index=False)
            
            print(f"✅ Data exported to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error exporting data: {e}")
            return None

def main():
    """Main function to demonstrate LSC Database functionality"""
    
    # Initialize the database manager
    lsc_db = LSCDatabaseManager()
    
    # Create the database
    print("🚀 Creating LSC Database...")
    db_path = lsc_db.create_database()
    
    # Show database information
    print("\n" + "="*60)
    lsc_db.get_database_info()
    
    # Show team summary
    lsc_db.get_team_summary()
    
    # Show example queries
    print("\n" + "="*60)
    print("📈 SAMPLE DATA QUERIES")
    print("="*60)
    
    print("\n1. 🥅 Top 10 Players by Disciplinary Actions:")
    player_stats = lsc_db.get_player_stats(10)
    if player_stats is not None:
        print(player_stats.to_string(index=False))
    
    print("\n2. ⚽ Recent Match Results:")
    recent_matches = lsc_db.get_recent_matches(8)
    if recent_matches is not None:
        print(recent_matches.to_string(index=False))
    
    print("\n" + "="*60)
    print("🎯 DATABASE READY FOR USE!")
    print("="*60)
    print("Available methods:")
    print("- lsc_db.query_database('YOUR_SQL_QUERY')")
    print("- lsc_db.get_player_stats(limit=10)")
    print("- lsc_db.get_recent_matches(limit=10)")
    print("- lsc_db.export_data('table_name', 'csv')")
    
    return lsc_db

if __name__ == "__main__":
    lsc_db = main()
