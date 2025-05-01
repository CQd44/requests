This is an extremely rudimentary ticketing system I made for the call center in which I work.

It's written in Python and utilizes PostgreSQL and a TOML file for certain configuration settings, such as a mail server and phone numbers to sent alerts to.

The modules that may need to be installed via pip are:
    fastapi
    psycopg2
    toml
    jinja2
    
The HTML files are what is live right now. 

The report generator script is EXTREMELY basic and really just spits everything from the database out into a CSV. 
