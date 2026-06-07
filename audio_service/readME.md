START
brew install python@3.10

/opt/homebrew/bin/python3.10 -m venv venv
# inside venv
source venv311/bin/activate
pip install -r requirements.txt

#wakeword model
<!-- import openwakeword
    openwakeword.utils.download_models() -->

# start
python -m app.main