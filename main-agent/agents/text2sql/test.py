import sqlite3
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from dotenv import load_dotenv
load_dotenv()

import os
password = os.getenv("POSTGRES_PASSWORD")

uri = f"postgresql://postgres:{password}@localhost:5432/daa"

# Initialize ChatOpenAI
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

# Create SQLDatabase instance - using our temporary database
db = SQLDatabase.from_uri(f"sqlite:///{temp_db_file}")

# Explore the database
explore_db(temp_db_file)

# Create SQL toolkit
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Create SQL agent
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

# Run the agent
result = agent.run("Do we have Alice in the database?")
print(result)

def explore_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n=== Database Explorer ===")
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("\nTables in database:")
    for table in tables:
        print(f"- {table[0]}")
        
        # Show schema for each table
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print("  Columns:")
        for col in columns:
            print(f"    {col[1]} ({col[2]})")
            
        # Show row count
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count}")
        
        # Show sample data
        cursor.execute(f"SELECT * FROM {table[0]} LIMIT 3")
        rows = cursor.fetchall()
        print("  Sample data:")
        for row in rows:
            print(f"    {row}")
        print()
    
    conn.close()

# Use it like this:
explore_db("temp_langchain_employees.db")

if __name__ == "__main__":
    main()