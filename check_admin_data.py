#!/usr/bin/env python3
import os
import psycopg2

# Use the same DB parameters as the import script
DB_PARAMS = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5438"),
    "database": os.environ.get("DB_NAME", "energy_model"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "password")
}

def check_admin_data():
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    print("=== Administrative Boundaries ===")
    cursor.execute("""
    SELECT level, COUNT(*) 
    FROM administrative_boundaries 
    GROUP BY level 
    ORDER BY level;
    """)
    
    for record in cursor.fetchall():
        print(f"{record[0]}: {record[1]} boundaries")
    
    print("\n=== Building Statistics Summary ===")
    cursor.execute("""
    SELECT 
        level,
        COUNT(*) as count,
        SUM(total_buildings) as total_buildings,
        SUM(electrified_buildings) as electrified_buildings,
        CAST(AVG(electrification_rate) AS DECIMAL(10,2)) as avg_electrification_rate,
        CAST(AVG(avg_consumption_kwh_month) AS DECIMAL(10,2)) as avg_consumption_kwh_month
    FROM administrative_boundaries ab
    JOIN building_statistics bs ON ab.id = bs.admin_id
    GROUP BY level
    ORDER BY level;
    """)
    
    for record in cursor.fetchall():
        print(f"{record[0]}: {record[1]} areas, {record[2]} buildings, {record[3]} electrified ({record[4]}%), avg consumption: {record[5]} kWh/month")
    
    print("\n=== Sample of Regions ===")
    cursor.execute("""
    SELECT id, name, parent_id
    FROM administrative_boundaries
    WHERE level = 'region'
    LIMIT 5;
    """)
    
    for record in cursor.fetchall():
        print(f"ID: {record[0]}, Name: {record[1]}, Parent: {record[2]}")
    
    print("\n=== Sample hierarchy check ===")
    cursor.execute("""
    SELECT 
        r.name as region,
        d.name as department,
        a.name as arrondissement,
        c.name as commune
    FROM administrative_boundaries r
    JOIN administrative_boundaries d ON d.parent_id = r.id
    JOIN administrative_boundaries a ON a.parent_id = d.id
    JOIN administrative_boundaries c ON c.parent_id = a.id
    WHERE r.level = 'region'
    LIMIT 3;
    """)
    
    for record in cursor.fetchall():
        print(f"Region: {record[0]} -> Department: {record[1]} -> Arrondissement: {record[2]} -> Commune: {record[3]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_admin_data() 