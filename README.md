# Stako
# Benjamin branch

What if you would like a more group-focused question and answer experience in sites like Stack Overflow?

This is a proof of concept project, where you can see a team view over Stack Overflow site. It uses Stack Overflow's API to retrieve data related to users, questions, and answers, to group activities around tags/technologies.

It has two components: a Restful API (inside `stako-api` folder), and the Stako website in the main folder. Both are built using Python3 and Flask.

## How to run it?

1. You will need a MongoDB. After installing it, configure the `settings.QAW_API_URL` on the main folder, to point to the MongoDB process.

2. Install the `requirements` using PIP or whatever you prefer. We recommend using a Python3 virtualenv for that.

3. Run the Flask API dev server:

    ```
    cd stako-api
    FLASK_APP=api.py flask run
    ```

4. Using another console, run the main site dev server:

    ```
    FLASK_RUN_PORT=8000 FLASK_APP=main.py flask run
    ```