#This is a custom-made script that utilizes FastAPI and PostgreSQL to give call center agents another way of letting me know
#they are experiencing an issue. 
#Additionally, it enables me to better keep track of what issues I fix and what remarks I may have made about the repair.
#I have also created a rudimentary report generator that will spit out everything in the database into a CSV.
#Written by Clay Young


from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import psycopg2
import easygui
import smtplib
import toml


CONFIG = toml.load("./config.toml") #load variables from toml file
app = FastAPI()
templates = Jinja2Templates(directory="templates") #loads HTML files from this directory
SERVER: str = CONFIG['comms']['server']
PORT: int = CONFIG['comms']['port']
FROM: str = CONFIG['comms']['from']
TO: list[str] = CONFIG['comms']['emails'] #list of emails to send responses to. currently unused.
PHONES: list[str] = CONFIG['comms']['phones']  #list of phone numbers 

#send text alert
def send_mms(user_name, clinic, issue):
    destination = ", ".join(PHONES)
    msg_text = f"""\
Subject: Issue Reported

User: {user_name}
Clinic: {clinic}
Issue: {issue}
"""

    with smtplib.SMTP(SERVER, PORT, timeout = 20) as server:
        server.ehlo()
        server.sendmail(from_addr = FROM, to_addrs= destination, msg = msg_text)
        server.quit()
        print("Text sent!")

# Set up postgresql database
def init_db():
    con = psycopg2.connect(f'dbname = {CONFIG['credentials']['dbname']} user = {CONFIG['credentials']['username']} password = {CONFIG['credentials']['password']}')
    cur = con.cursor()
    cur.execute("""SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'responses'
                );""")
    responses_table_exists: bool = cur.fetchone()
    print(responses_table_exists)
    if responses_table_exists[0] == False: 
        con = psycopg2.connect(f'dbname = {CONFIG['credentials']['dbname']} user = {CONFIG['credentials']['username']} password = {CONFIG['credentials']['password']}')
        cur = con.cursor()
        cur.execute('''CREATE TABLE responses 
                    (id SERIAL PRIMARY KEY, 
                    Name TEXT,
                    Clinic TEXT, 
                    Issue TEXT,
                    EntryDate TIMESTAMPTZ DEFAULT Now(),
                    Open BOOL DEFAULT True,
                    Remarks TEXT)'''
                )
        cur.close()
        con.commit()

# Home page with the form
@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

# Handle form submission
@app.post("/submit")
async def submit_form(name: str = Form(...), clinic: str = Form(...), response: str = Form(...)):
    con = psycopg2.connect(f'dbname = {CONFIG['credentials']['dbname']} user = {CONFIG['credentials']['username']} password = {CONFIG['credentials']['password']}')
    cur = con.cursor()
    cur.execute("INSERT INTO responses (Name, Clinic, Issue) VALUES (%s, %s, %s)", (name.strip(), clinic.strip(), response.strip()))    
    cur.execute("SELECT id FROM responses ORDER BY id DESC LIMIT 1")
    new_id = cur.fetchone()[0]
    cur.close()
    con.commit()
    send_mms(name, clinic, response)
    return RedirectResponse(url=f"/thank-you?id={new_id}", status_code=303)

# Thank-you page
@app.get("/thank-you", response_class=HTMLResponse)
async def thank_you(request: Request, id: int = None):
    return templates.TemplateResponse("thank_you.html", {"request": request, "id" : id})

#Page to let users check on their ticket if they search by ID
@app.get("/view", response_class = HTMLResponse)
async def view_ticket(request: Request, id: int):
    con = psycopg2.connect(f'dbname = {CONFIG['credentials']['dbname']} user = {CONFIG['credentials']['username']} password = {CONFIG['credentials']['password']}')
    cur = con.cursor()
    cur.execute(f"SELECT * FROM responses WHERE id = {id}")
    
    result = cur.fetchone()
    cur.close()

    if result:
        ticket_data = {"id" : result[0], "name" : result[1].strip(), "clinic" : result[2].strip(), "issue" : result[3].strip(), "entrydate" : result[4], "open" : result[5], "Remarks" : result[6]}
        return templates.TemplateResponse("view_row.html", {"request" : request, "ticket_data" : ticket_data})
    else:
        return HTMLResponse(content="<h1>Ticket not found.</h1><a href = '/'>Go back</a>")

# Initialize the database when the app starts
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
    except Exception as e:
        print("Table already exists")