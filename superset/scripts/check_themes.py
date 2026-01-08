"""Check themes in database."""
from superset import db
from sqlalchemy import text

result = db.session.execute(text("SELECT id, name FROM themes")).fetchall()
print("=== THEMES IN DATABASE ===")
for row in result:
    print(f"  ID: {row[0]}, Name: {row[1]}")
if not result:
    print("  (no themes found)")
