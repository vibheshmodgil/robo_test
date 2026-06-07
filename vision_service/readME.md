START
brew install python@3.11

g
# inside venv
source venv311/bin/activate
pip install -r requirements.txt

# start
python -m app.main


# WIDNOWS 
winget install python@3.11
py -m venv venv
pip install -r requirements.txt
venv\Scripts\activate
