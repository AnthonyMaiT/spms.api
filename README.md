# Student Point Management System App

This project was created using [Python 3.8](https://docs.python.org/3.8/) and [Angular](https://angular.io/) in Windows 11

## Prerequisites

- [Python 3.8](https://www.python.org/downloads/)
- [Visual Studio Code](https://code.visualstudio.com/download)
- [Node.JS v18](https://nodejs.org/en/download/)

## Database Setup

Install [PostgreSQL 15.1 with StackBuilder](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) and create a database
Optionally, if you want to schedule backups, open StackBuilder during the installation and install pgAgent.

## Setting up the API Environment
Create an .env file at root of the spms.api folder and set the following environment variables
Example:
`DATABASE_HOSTNAME = localhost`
| Variable Name | Value  |
| ------- | --- |
| DATABASE_HOSTNAME | Hostname of the database. |
| DATABASE_PORT | Port of the database. |
| DATABASE_NAME | Name of the database |
| DATABASE_USERNAME | Username to connect to the database. |
| DATABASE_PASSWORD | Password for the username. |
| SECRET_KEY | 32bit Hexadecimal. |
| ALGORITHM | JWT Algorithm (Preferred: HS256) |
| ACCESS_TOKEN_EXPIRE_MINUTES | Length of expiration for logged in. |

Optionally, you can set up a [Python Enviornment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) to run this app

To install all the packages, run the following command in command prompt in the spms.api folder:
`pip install -r requirements.txt`

In main.py in the app folder, you can change the CORS origin in the list to allow certain URLS to access the API

Now you can run the following command to start the app:
`uvicorn app.main:app --reload`
The app would run at http://localhost:8000

API Documentation is at http://localhost:8000/docs

## Setting up the Frontend
SPMS.ui was generated with [Angular CLI](https://github.com/angular/angular-cli) version 14.2.10.

In the SPMS.UI folder in command prompt, run the following command to install node_modules:
`npm install`

Go to the src/enviornments folder in your SPMS.UI app
In both environment files (One for development and one for production), you can set the URL of the API

#### Development server

Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The application will automatically reload if you change any of the source files.
Default Admin Username: admin
Default Admin Password: 123qwe

#### Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

#### Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory.

#### Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

#### Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via a platform of your choice. To use this command, you need to first add a package that implements end-to-end testing capabilities.

#### Further help

To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI Overview and Command Reference](https://angular.io/cli) page.


## Optional: Schedule Database Backups
As pgAgent is installed, you should see a postgres folder in your Users folder of your Local Disk.
Go to `C:\Users\postgres\AppData\Roaming\postgresql` and you should see pgpass.conf. If not found, you can create it.
Open the config file and add the following line: 
`{hostname of your db}:{port number of db}:{db name}:{username for db}: {password}`

In the database, right click extensions and select "Query Tool".
Type in `CREATE EXTENSION pgagent;` and run the query.

Below "Databases" right click "pgAgent Jobs" and create a new job.
Add a name and then go to the "Steps" tab.
Create a new step that uses Batch and then go to "Code".

Add the following code:
`C:\"Program Files"\PostgreSQL\15\bin\pg_dump.exe --file "{filepath}\\{backup name}}.sql" --dbname={name of db} --username={username for db} --clean`
(Keep in mind that this is ran under the postgres user account so filepath have correct permission for it.)

If you want the date and time to show you can do:
`@echo off`\
`For /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)`\
`For /f "tokens=1-2 delims=/:" %%a in ("%TIME%") do (set mytime=%%a%%b)`\
`C:\"Program Files"\PostgreSQL\15\bin\pg_dump.exe --file "{{filepath}}\\{backup name}}-%mydate%_%mytime%.sql" --dbname=spms --username=postgres --clean`

To schedule, go to the schedules tab and create a new schedule.
Set the start and end of the schedule and then you can add repeated date or time in the repeat tab.

## Optional: Customize Chatbot
In the `/chatbot/intents` folder, you are able to edit the messages the bot sents to all the different role types. If you want to customize the intents of the user, then you can follow the format that is given in the json file. Then, in command prompt/terminal, go to the chatbot folder and type the following command:
`python train.py`
Then you will be ready to go!

## CREDITS

Chatbot was created from (this)[https://github.com/patrickloeber/chatbot-deployment] git repository which was also inspired by (this)[https://chatbotsmagazine.com/contextual-chat-bots-with-tensorflow-4391749d0077] article. Front end chatbot's html and css was created using (this)[https://github.com/hitchcliff/front-end-chatjs]