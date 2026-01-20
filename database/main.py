
from fastapi import FastAPI, Depends
from . import models, schemas
from .database import engine, get_db, init_db
from sqlalchemy.orm import Session

#models.Base.metadata.create_all(bind=engine)
init_db()
app = FastAPI()




# while True:
#     try:
#         conn = psycopg.connect("host=localhost dbname=gdf_meta " \
#         "user=gdf password=gdf_password" )
#         cur = conn.cursor()
#         print("connection sucessful")
#         break
#     except Exception as e:
#         print(f"connection failed {e}")
#         time.sleep(2)



@app.get("/sqlalchemy")
def test_posts(db: Session = Depends(get_db)):
    dq = db.query(models.DqRun).all()
    return {"data": "sucessful"}


@app.get("/")
async def root():
    
    return {"hello": "world"}



# while True:
#     try:
#         conn = psycopg.connect("host=localhost dbname=gdf_meta " \
#         "user=gdf password=gdf_password" )
#         cur = conn.cursor()
#         print("connection sucessful")
#         break
#     except Exception as e:
#         print(f"connection failed {e}")
#         time.sleep(2)

  # get data from   dq_runs table
  #     
