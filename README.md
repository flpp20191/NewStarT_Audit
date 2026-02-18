# NewStarT

## Description
NewStarT audit is a **no-coding shell of a rule-based expert system** designed to give recomendations based on category match.
It is an open-source framework developed using Python and the Django framework.
 
Key Features and Concepts:
- **Rule-Based Expert System:** It allows domain experts to define and manage "if-then" rules without needing to delve into technical coding aspects.
- **Digital Twin Paradigm:** The system architecture incorporates the concept of a digital twin, a virtual representation of a physical system.
- **Purpose:** The primary goal is to provide a user-friendly tool that can be used to generate questionnaires from OWL to make a recommendation system.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1: Clone the Repository](#step-1-clone-the-repository)
- [Step 2: Create a Virtual Environment](#step-2-create-a-virtual-environment)
- [Step 3: Install Dependencies](#step-3-install-dependencies)
- [Step 4: Configure the Database and Environment Variables](#step-4-configure-the-database-and-environment-variables)
- [Step 5: Run the Setup Command](#step-5-run-the-setup-command)
- [Step 6: Upload the OWL file](#step-6-upload-the-owl-file)
- [Step 7: Run the Development Server](#step-7-run-the-development-server)
- [Additional Commands](#additional-commands)
- [Deactivating the Virtual Environment](#deactivating-the-virtual-environment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Before you begin, make sure you have the following installed on your system:

- **Python 3.x**: [Download Python](https://www.python.org/downloads/)
- **pip**: Python's package installer (included with Python 3.x)
- (optional) **MySQL** : Ensure that MySQL is installed and running on your machine if you choose to use them.

## Step 1: Clone the Repository

Start by cloning the repository to your local machine:

```bash
git clone https://github.com/flpp20191/NewStarT_Audit
cd NewStarT_Audit
```

## Step 2: Create a Virtual Environment

It’s recommended to use a virtual environment to manage project dependencies. Follow the instructions below based on your operating system.

### On macOS and Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

After activating the virtual environment, you should see `(venv)` at the beginning of your command line prompt.

## Step 3: Install Dependencies

With the virtual environment activated, install the required Python packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

This command will install all necessary packages for the Django project.

## Step 4: Configure the Database and Environment Variables

The project can be configured to use SQLite or MySQL. By default, Django is configured to use SQLite, but you can switch to another database if needed.

### 1. **Copy `Example/.env.example` to `.env`**:

In the root of your project directory, copy the `Example/.env.example` file to create a new `.env` file:

#### On macOS/Linux:

```bash
cd root
cp ./Example/.env.example .env
```

#### On Windows:

```bash
cd root
copy ./Example/.env.example .env
```

### 2. **Generate a Secure `SECRET_KEY`**:

To ensure the `SECRET_KEY` is secure, generate a random key by running the following command:

```bash
python
from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())
```

This will output a secure key that you should copy and paste into your `.env` file under the `SECRET_KEY` variable:

```bash
SECRET_KEY=placeholder_generated_secret_key
```

### 3. **Configure the Database**:

In your `.env` file, set the `DB_ENGINE` to select which database backend you want to use. The available options are `sqlite3`, `mysql`.

#### **Default SQLite Setup**

If you want to use SQLite (default setup), set the following in your `.env` file:

```bash
DB_ENGINE=sqlite3
```

The default SQLite configuration requires no additional setup. It will create a `db.sqlite3` file in the project directory.

#### **Optional MySQL Setup**

To use MySQL, set the following in your `.env` file:

```bash
DB_ENGINE=mysql
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=3306
```

Ensure that your MySQL server is up and running before proceeding.

## Step 4: Set up score update frequency

The `SCORE_UPDATE_DELAY` defines the minimum ammount of time someone has to wait, to recalculate their scores.

```bash
SCORE_UPDATE_DELAY=300
```

## Step 5: Run the Setup Command

After configuring the environment variables, run the setup command to create the database, apply migrations, and populate initial data:

```bash
cd..
python manage.py setup
```

This command will:

- Connect to the database using the credentials from the `.env` file.
- Create the database (if it doesn't already exist).
- Run all Django migrations to set up the database schema.

## Step 6: Upload the OWL file

After running the setup command, you can upload an OWL file to the system from example, or use your own ontology.
To upload the Example file run this command.

```bash
cd..
python manage.py uploadOwl --filepath Example/NewStarT.owl --language en --make_config --config_filename Example/conf_output.yml --conf Example/conf.yml
```

Command parameter:
- *`--filepath __filepath__` - local/global path to the OWL file
- *`--language __language__` - language tag used in label (e.g. en, lv)
- `--make_config` - ability to make config file to speed OWL upload next time (!Will only work if Object, Data and answer type IRIs are not changed!)
- `--config_filename` - output file path for configuration file
- `--conf` - configuration file to reduce needed user input

To upload your own OWL file, follow instructions in the command.
Expected file structure

File structure:
- .owl (or any other Python owlready2 compatible format)
- Data and Object property names can be changed to anything, only the relation structure matters

- (Required) ategory relationship format: 'Question(Class)'->hasSomeObjectProperty->'Category(Class)
- (For multi question type) Expected question type format: 'QuestionType(Class)'->hasSomeObjectProperty->'YesNo(Class)'
- (For Likerta) Expected likerta answer choice format: 'hasAnswerOptions(DataProperty)' value 'Answer option text'(str)
- (For Likerta) Expected likerta answer format: 'hasAnswer(DataProperty) value 'Answer option'(str)
- (For Interval) Expected min answer range format: 'hasMinValue(DataProperty) value '0'(flaot)
- (For Interval) Expected max answer range format: 'hasMaxValue(DataProperty) value '100'(flaot)
- (Optional) Expected higlighted question format: 'required(DataProperty) value 'true'(bool)
- (Optional) Expected question group format: 'Question(Class)'->hasGroup->'Group(Class)
- (Optional) Expected hint text format: 'Question(Class)'->hasHintText->'Hint(Class)

This command will:
- Read the data structure of the OWL file.
- Ask you to specify which properties corespond to which data structures.
- Update the DB only if all changes are valid.
- (Optional) Generate configuration file to speed up OWL upload the next time.

## Step 7: Run the Development Server

Once the setup is complete, start the Django development server:

```bash
python manage.py runserver
``` 

Visit `http://127.0.0.1:8000/` in your web browser to see the project in action.

## Creating a Superuser

To create a superuser account for accessing the Django admin interface, run:

```bash
python manage.py createsuperuser
```

Follow the on-screen prompts to set up the username, email, and password. Use superuser credentials to access system.

## Additional Commands


### Running Tests

If the project includes tests, you can run them with:

```bash
python manage.py test
```

## Deactivating the Virtual Environment

When you are done working on the project, deactivate the virtual environment by running:

```bash
deactivate
```

## Troubleshooting

- **Database Connection Issues**: Ensure that your database server is running and that the credentials in the `.env` file are correct.
- **Missing Packages**: If you encounter missing package errors, verify that your virtual environment is activated before running any commands.

## Contributing

If you'd like to contribute to this project, you can fork the repository and submit a pull request with your changes.

Copyright 2026 NewStarT

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


