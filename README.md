# SDA Church Eden Springs Camp Meeting Project

This is a Django-based web application for managing contributions and payments for the Eden Springs SDA Church Camp Meeting 2025. It supports M-Pesa STK Push payments, real-time contribution statistics, finance reporting (with PDF export), and user authentication for finance/admin users.

---

## Features

- **Landing Page:** Countdown to event, contribution stats, and latest contributions.
- **M-Pesa Integration:** STK Push payment initiation and status polling (no callback required).
- **Contribution Tracking:** Stores all contributions, verifies payments, and saves Mpesa codes.
- **Finance Report:** View and export all successful transactions as a PDF.
- **User Authentication:** Login/logout for finance/admin users.
- **Session Timeout:** Users are logged out after inactivity for security.
- **Responsive UI:** Built with Tailwind CSS and DaisyUI.

---

## Requirements

- Python 3.8+
- Django 3.2+
- WeasyPrint (for PDF export)
- requests, python-dotenv
- M-Pesa Daraja API credentials

---

## Setup

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd SDA-CHURCH-EDEN-SPRINGS
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Install WeasyPrint system dependencies:**
   - On Windows, download and install [GTK3+ runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) and add its `bin` folder to your PATH.
   - See [WeasyPrint installation docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).

5. **Set up environment variables:**
   - Copy `.env.example` to `.env` and fill in your M-Pesa and email credentials.

6. **Run migrations:**
   ```sh
   python manage.py migrate
   ```

7. **Create a superuser:**
   ```sh
   python manage.py createsuperuser
   ```

8. **Run the development server:**
   ```sh
   python manage.py runserver
   ```

---

## Usage

- **Landing Page:** `/`
- **Contribute:** `/contribute/` (via landing page form)
- **Check Payment Status:** Handled automatically via frontend polling `/stk_status/`
- **Finance Report:** `/finance-report/` (login required)
    - Export PDF: `/finance-report/?format=pdf`
- **Login:** `/login/`
- **Logout:** `/logout/`

---

## Project Structure

```
camp_meeting_project/
├── camp_meeting/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── templates/
│   │   └── camp_meeting/
│   │       ├── landing.html
│   │       ├── login.html
│   │       └── finance_report.html
│   └── ...
├── manage.py
└── ...
```

---

## Key Files

- **models.py**: Contribution and settings models.
- **views.py**: All business logic (payments, stats, login, finance report, etc).
- **templates/camp_meeting/**: All HTML templates.
- **urls.py**: URL routing for the app.

---

## Security

- Only authenticated users can access the finance report.
- Sessions expire after inactivity (see `SESSION_COOKIE_AGE` in `settings.py`).

---

## Customization

- Update event dates, target amount, and branding in `views.py` and templates.
- Adjust session timeout in `settings.py` as needed.

---

## Troubleshooting

- **WeasyPrint errors:** Ensure GTK3+ is installed and in your PATH.
- **M-Pesa issues:** Check your credentials and Safaricom Daraja API status.
- **PDF export issues:** Use simple CSS, avoid unsupported properties like `color-scheme`.

---

## License

This project is for Eden Springs SDA Church and is not licensed for commercial use.

---

## Contact

For support, contact the project maintainer or Eden Springs SDA Church IT