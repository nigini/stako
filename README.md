# qaworld-teams
What if you would like a more group-focused question and answer experience in sites like Stack Overflow?

This is a proof of concept project, where you can see a team view over Stack Overflow site. It basically uses Stack Overflow's API to retrieve questions related to tags and present it in different ways.

You will need a MongoDB (which we use to store retrieved info locally). After having that, configure the settings, install the requirements using PIP or whatever you prefer, and run the Flask dev server: 

    FLASK_APP=main.py flask run
