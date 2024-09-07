import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import pandas_udf, expr
import pandas as pd


spark = SparkSession.builder.getOrCreate()  # create spark session

df = spark.createDataFrame([
    ['red', 'banana', 1, 10],
    ['blue', 'banana', 2, 20],
    ['red', 'carrot', 3, 30],
    ['blue', 'grape', 4, 40],
    ['red', 'carrot', 5, 50],
    ['black', 'carrot', 6, 60],
    ['red', 'banana', 7, 70],
    ['red', 'grape', 8, 80]
], schema=['color', 'fruit', 'v1', 'v2'])

########################################################################################################################

# Case №1
df.createOrReplaceTempView("tableA")
spark.sql("SELECT COUNT(*) AS Qty FROM tableA").show()

# Case №2


@pandas_udf("integer")
def add_one(s: pd.Series) -> pd.Series:
    return s + 1


spark.udf.register("add_one", add_one)
spark.sql("SELECT add_one(v1) FROM tableA").show()

# Case №3
df.selectExpr('add_one(v1)').show()
df.select(expr('count(*)') > 0).show()
