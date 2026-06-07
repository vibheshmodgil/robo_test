START
brew install python@3.11

python3.11 -m venv venv
# inside venv
source venv/bin/activate
pip install -r requirements.txt

# start
python -m app.main