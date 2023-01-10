# Introduction 
<p>The key_generation python script will be executed threw an api and will execute the deposit.sh script tp generate validator data payloads.</p>
<p>It generate a password, generate a mnmemonic, store the data in relative tables using Fernet and PGP encryptions, send the right information to the node api to execute the keys_handler script and remove the two generated files.</p>

# 0ffchain scrips
1. [event_listener](https://github.com/SkyzoNams/event_listener)
2. [records_handler](https://github.com/SkyzoNams/records_handler)
3. [key_generation](https://github.com/SkyzoNams/key_generation)
4. [scheduled_action](https://github.com/SkyzoNams/scheduled_action)
5. [keys_handler](https://github.com/SkyzoNams/keys_handler)

# Getting Started
1.	Clone the repo
2.  Make sure to have Python 3 installed on your machine (developed with Python 3.7.8)
3.  Go inside the project root you want to execute (/event_listener)
4.  Create your local venv by doing "python3 -m venv ./venv"
5.  Activate the venv by doing "source venv/bin/activate"
6.	From the project rool install all the dependencies by doing "pip install -r requirements.txt"
