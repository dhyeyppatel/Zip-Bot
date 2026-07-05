import asyncio; from pony.orm import *; db = Database(); db.bind('sqlite', ':memory:', create_db=True); class User(db.Entity): pass; db.generate_mapping(create_tables=True); 
async def test():
  with db_session:
    pass
asyncio.run(test())
