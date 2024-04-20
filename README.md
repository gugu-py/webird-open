# Webird

> A birding record management project built on Django and database

This project is like an open-source and simpler version of Ebird, but it distinguishes locations using categorical data.

## Current Features
### For Guests
- display bird distribution on a map (image) with clickable place markers
- search records by species/class/location/time_interval
- visualize the searched records
- search images uploaded by admins by species/class/location/time_interval/description

### For Admins(login-required users)
- All functions of guests
- add/edit new location marker
- add/edit new bird species
- add/edit new bird class
- add/edit birding record
- add new images(support both third-party image host and local image host)

## How to use
Clone this project using `git clone https://github.com/gugu-py/webird-open.git`

Make your working directory the project's directory. Then install the dependency using `pip install -r requirements.txt`

Run the program. `python manage.py` Type `localhost:8000` into your browser to preview the website.

### Custom
This is a classical django project. The way to custom it is the same with other typical django projects.

## Credit
- Design and coding: myself
- Icon Design: Jimmy Cheng
- A friend who helped me with deploying
- A friend who is always patient to help me with bugs and answer my questions
- My parents who have been supporting me mentally, and give me time to develop my interest
