# LSC Database Usage Examples
# Run this after creating your database with LSC_enhanced.py

from LSC_enhanced import LSCDatabaseManager

# Initialize the database
lsc_db = LSCDatabaseManager()

# Example 1: Get all players with their positions
players_query = """
    SELECT 
        "Unnamed__0_level_0_Player" as Player_Name,
        "Unnamed__1_level_0_Nation" as Nationality,
        "Unnamed__2_level_0_Pos" as Position,
        "Performance_CrdY" as Yellow_Cards,
        "Performance_CrdR" as Red_Cards
    FROM player_disciplinary 
    WHERE Player_Name NOT IN ('Squad Total', 'Opponent Total')
    ORDER BY Yellow_Cards DESC
"""

print("🥅 PLAYER DISCIPLINARY RECORDS:")
players = lsc_db.query_database(players_query)
print(players.head(10))

# Example 2: Home vs Away Performance
home_away_query = """
    SELECT 
        Venue,
        COUNT(*) as Matches,
        SUM(CASE WHEN Result = 'W' THEN 1 ELSE 0 END) as Wins,
        SUM(CASE WHEN Result = 'D' THEN 1 ELSE 0 END) as Draws,
        SUM(CASE WHEN Result = 'L' THEN 1 ELSE 0 END) as Losses,
        AVG(GF) as Avg_Goals_For,
        AVG(GA) as Avg_Goals_Against
    FROM match_results 
    WHERE Result IS NOT NULL
    GROUP BY Venue
"""

print("\n🏠 HOME vs AWAY PERFORMANCE:")
home_away = lsc_db.query_database(home_away_query)
print(home_away)

# Example 3: Competition Performance
competition_query = """
    SELECT 
        Comp as Competition,
        COUNT(*) as Matches_Played,
        SUM(CASE WHEN Result = 'W' THEN 1 ELSE 0 END) as Wins,
        SUM(CASE WHEN Result = 'D' THEN 1 ELSE 0 END) as Draws,
        SUM(CASE WHEN Result = 'L' THEN 1 ELSE 0 END) as Losses
    FROM match_results 
    WHERE Result IS NOT NULL
    GROUP BY Comp
"""

print("\n🏆 PERFORMANCE BY COMPETITION:")
competitions = lsc_db.query_database(competition_query)
print(competitions)

# Example 4: Export data to CSV
print("\n📁 EXPORTING DATA:")
lsc_db.export_data('player_disciplinary', 'csv')
lsc_db.export_data('match_results', 'csv')

print("\n✅ Database examples completed!")
