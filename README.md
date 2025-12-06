# ad-dawah-ilallah-backend
**Ad Dawah Ilallah Digital Campus (E-Maktab)** is a comprehensive web-based educational and organizational management system designed to centralize and digitize the
activities of **Ad Dawah Ilallah Institute.**

The platform will serve as an **electronic campus**, integrating student management, teacher management, academic operations, financial tracking, program registrations, consultation services, and organizational activities under one cohesive ecosystem.

It will ensure:
- Centralized access for administrators, teachers, students, and coordinators.
- Smooth usability across PC and mobile devices.
- Secure and scalable backend architecture.
- Integration with existing Ad Dawah Ilallah digital services (e.g., Dawah ilallah App,Nibrash, Al-Itisam).


ER Diagram link of the database: https://dbdiagram.io/d/Ad-Dawah-Ilallah-692181cc228c5bbc1a02b493


## System Requirements:
- *`Ubuntu v20.04 LTS or higher (like 24.04 LTS)`*
- *`Python v3.11.x or higher (like 3.12.x)`*<sup>`python3.11` for ubuntu `20.04 LST` and `python3.12` for Ubuntu `24.04 LTS`</sup>
- *`Django v5.2 LTS`*
- *`PostgreSQL`*<sup>`v16.x (recommended)`</sup>

## Installation
- **Clone the repository:** `git clone https://github.com/nasimul007/ad-dawah-ilallah-backend`
- **Create virtual environment:** `virtualenv -p python3.x <env_name>`
- **Install dependencies:** `pip install -r requirements.txt`
- **Setup .env:** `Create .env file and copy all variable from .env.example and put respective value`
- **Database migrations:**` python manage.py migrate`
- **Load initial data (optional):** `python manage.py loaddata import_data/*.json`
- **Start the Django development server:** `python manage.py runserver`