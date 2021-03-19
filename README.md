# Stako

STAKO is a research-focus tool created at the WildLab in the University of Washington to enable running experiments with users of Stack Overflow. Our goals is to improve how users experience SO and to include more people in the conversation.

It has three components: a Restful API (inside `stako-api` folder), a Browser extension (inside `stako-browser`) and a website in the `stako-site` folder *(!!! right now under-developed !!!)*. We mainly used Python3 and Flask for the backend components, and basic web-technology like Javascript, JQuery and CSS for the frontend.

## How to run Stako Server?

1. You will need a MongoDB. After installing it, configure the `stako.settings` inside the `stako-api` to point to the MongoDB process. We provide a model for this file, just copy it and change the information about the DB.

2. Install the `requirements` using PIP or whatever you prefer. We recommend using a Python3 [virtualenv](https://pythonbasics.org/virtualenv/) for that.

```
?> source [VENV_PATH}/bin/activate
(VENV) ?> python3 -m pip install -r requirements.txt
(VENV) ?> cd stako-api
```

3. Run the unit_tests to check if everything is set correctly.

```
(VENV) ?/stako-api/> python3 -m unittest stako/api/data/test/*.py
(VENV) ?/stako-api/> python3 -m unittest stako/api/test/*.py
```

4. Run the Flask API dev server:

```
(VENV) ?/stako-api/> FLASK_APP=stako.api.api flask run
```

You'll probably see something like `INFO:werkzeug: * Running on http://127.0.0.1:5000/` and that means that you have a stako-api server running at that URL. You can go to a browser now and access something like `127.0.0.1:5000/v1/user/test/`. But, as you have no registered or authenticated user, you'll get a `401` HTTP error, which is great, meaning that the API is not accepting your unauthorized call.

### Adding real data

**TODO!**

### Production server

**TODO!**


