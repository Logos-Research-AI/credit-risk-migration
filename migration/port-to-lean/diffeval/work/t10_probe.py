import polars as pl
df = pl.DataFrame({"row_id": [1.0], "age": [3.0], "x": [1.0]})
for m in ({"age": "age"}, {"age": "Age"}, {"age": "row_id"}):
    try:
        print(m, df.rename(m).columns)
    except Exception as e:
        print(m, type(e).__name__, str(e)[:80])
try:
    print(df.drop("age").rename({"age": "AGE"}).columns)
except Exception as e:
    print("absent", type(e).__name__, str(e)[:80])
