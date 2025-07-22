# libraries
import pandas as pd
import sqlite3
from datetime import datetime
import os

# fbref table link
url_df = 'https://fbref.com/en/squads/7622315f/Lexington-SC-Stats'

def create_lsc_database():
    """Create and populate LSC database with all stats"""
    
    # Create database connection
    db_path = 'lsc_database.db'
    conn = sqlite3.connect(db_path)
    
    print("Fetching data from FBRef...")
    # Get all tables from the webpage
    tables = pd.read_html(url_df)
    
    print(f"Found {len(tables)} tables on the page")
    
    # Process each table and save to database
    table_names = []
    
    for i, table in enumerate(tables):
        # Clean column names for multi-index tables
        if hasattr(table.columns, 'nlevels') and table.columns.nlevels > 1:
            table.columns = [' '.join(col).strip() for col in table.columns]
        
        # Reset index
        table = table.reset_index(drop=True)
        
        # Determine table type based on content
        table_name = determine_table_type(table, i)
        table_names.append(table_name)
        
        # Clean and save table to database
        clean_table = clean_dataframe(table)
        clean_table.to_sql(table_name, conn, if_exists='replace', index=False)
        
        print(f"Saved table {i+1}: {table_name} ({len(clean_table)} rows, {len(clean_table.columns)} columns)")
    
    # Create metadata table
    create_metadata_table(conn, table_names)
    
    conn.close()
    print(f"\nDatabase created successfully: {db_path}")
    return db_path

def determine_table_type(df, table_index):
    """Determine what type of table this is based on content"""
    
    # Check column names to identify table type
    columns = [str(col).lower() for col in df.columns]
    
    if any('player' in col for col in columns):
        if any('gk' in col or 'goalkeeper' in col or 'save' in col for col in columns):
            return 'goalkeeper_stats'
        elif any('performance' in col or 'disciplinary' in col for col in columns):
            return 'player_performance'
        elif any('xg' in col or 'expected' in col for col in columns):
            return 'player_advanced_stats'
        else:
            return 'player_standard_stats'
    
    elif any('date' in col or 'comp' in col or 'opponent' in col for col in columns):
        return 'match_fixtures'
    
    elif any('squad' in col or 'team' in col for col in columns):
        if any('home' in col and 'away' in col for col in columns):
            return 'league_standings_detail'
        else:
            return 'league_standings'
    
    else:
        return f'table_{table_index + 1}'

def clean_dataframe(df):
    """Clean dataframe for database storage"""
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Replace NaN with None for better SQLite compatibility
    df = df.where(pd.notnull(df), None)
    
    # Clean column names - remove special characters
    df.columns = [col.replace('/', '_').replace(' ', '_').replace('-', '_').replace('+', '_plus_') 
                  for col in df.columns]
    
    return df

def create_metadata_table(conn, table_names):
    """Create a metadata table with information about the database"""
    metadata = pd.DataFrame({
        'table_name': table_names,
        'created_date': [datetime.now().isoformat()] * len(table_names),
        'source_url': [url_df] * len(table_names)
    })
    metadata.to_sql('database_metadata', conn, if_exists='replace', index=False)

def query_database(db_path, query):
    """Execute a query on the database"""
    conn = sqlite3.connect(db_path)
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result

def get_table_info(db_path):
    """Get information about all tables in the database"""
    conn = sqlite3.connect(db_path)
    
    # Get all table names
    tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
    tables = pd.read_sql_query(tables_query, conn)
    
    print("Tables in LSC Database:")
    print("=" * 40)
    
    for table_name in tables['name']:
        # Get row count
        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        count = pd.read_sql_query(count_query, conn)['count'][0]
        
        # Get column info
        columns_query = f"PRAGMA table_info({table_name})"
        columns = pd.read_sql_query(columns_query, conn)
        
        print(f"\n{table_name.upper()}:")
        print(f"  Rows: {count}")
        print(f"  Columns: {len(columns)}")
        print(f"  Column names: {', '.join(columns['name'].tolist())}")
    
    conn.close()

if __name__ == "__main__":
    # Create the database
    db_path = create_lsc_database()
    
    # Show database information
    print("\n" + "="*50)
    get_table_info(db_path)
    
    # Example queries
    print("\n" + "="*50)
    print("EXAMPLE QUERIES:")
    print("="*50)
    
    try:
        # Get player stats
        print("\n1. Top 10 Players by Goals + Assists:")
        player_stats = query_database(db_path, """
            SELECT Player, Nation, Pos, Gls, Ast, G_plus_A_minus_PK 
            FROM player_standard_stats 
            WHERE Player != 'Squad Total' AND Player != 'Opponent Total'
            ORDER BY G_plus_A_minus_PK DESC 
            LIMIT 10
        """)
        print(player_stats)
        
        # Get recent matches
        print("\n2. Recent Matches:")
        matches = query_database(db_path, """
            SELECT Date, Time, Comp, Venue, Result, Opponent 
            FROM match_fixtures 
            WHERE Date IS NOT NULL 
            ORDER BY Date DESC 
            LIMIT 5
        """)
        print(matches)
        
    except Exception as e:
        print(f"Error running example queries: {e}")
        print("You can run custom queries using: query_database(db_path, 'YOUR_SQL_QUERY')")