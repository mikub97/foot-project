import sqlite3

from listener import prepare
from manufacture import getTracesBetweenTimes, createScatterPlot
conn = sqlite3.connect("realtime.db", check_same_thread=False)#DB connection
c = conn.cursor()
prepare()
df = getTracesBetweenTimes(conn, "Grzegorczyk", "2021-01-27 19:08:47", "2021-01-27 19:10:36", 100)
createScatterPlot(df)

