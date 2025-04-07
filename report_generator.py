import csv
import psycopg2
import easygui #might implement more functionality later and I like easygui :)
from icecream import ic
import toml

CONFIG = toml.load("./config.toml") #load configuration variables from toml file
COLUMNS: list[str] = ['id', 'name', 'clinic', 'issue', 'entrydate', 'open', 'remarks']
RESULTS: list[any] = []

con = psycopg2.connect(f'dbname = {CONFIG['credentials']['dbname']} user = {CONFIG['credentials']['username']} password = {CONFIG['credentials']['password']}')
cur = con.cursor()

cur.execute("SELECT * FROM responses")
rows = cur.fetchall()

for row in rows:
    subresult = []
    for i in range(len(COLUMNS)):
        subresult.append(row[i])
    RESULTS.append(subresult)

with open('report.csv', 'w', newline = '') as report:
    writer = csv.writer(report)
    writer.writerow(COLUMNS)
    for row in RESULTS:
        writer.writerow(row)