import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import random

# Email Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'email@example.com'
SMTP_PASSWORD = 'KEYEXAMPLE'

# Student Emails
students = [
    'email@example.com',
    'email@example.com',
    'student3@example.com',
    'student4@example.com'
]

# Weekly Schedule: (Start Date: (Topic, Presenter))
schedule = {
    '2025-03-14': ('Climate & Climate Change', 'João'),
    '2025-03-21': ('Risks & Risk Management', 'Clara'),
    '2025-03-28': ('Resources & Resource Management', 'Barbara'),
    '2025-04-04': ('Geomorphology & Land Use', 'Barbara'),
    '2025-04-11': ('Land Forms', 'João and Clara'),
    '2025-04-18': ('Population & Population Changes', 'Isabela'),
    '2025-04-22': ('2nd Specialist: Clibson’s Class', 'Specialist'),
    '2025-04-25': ('Weather and Erosion', 'Barbara and João'),
    '2025-05-02': ('TBD', 'TBD'),
    '2025-05-09': ('Agricultural Geography & Food Issues', 'Isabela and Clara'),
    '2025-05-16': ('Environmental Geography & Sustainable Development', 'Isabela'),
    '2025-05-23': ('Economic Geography & Globalization', 'Barbara'),
    '2025-05-30': ('Coast Management', 'Isabela and Clara'),
    '2025-06-06': ('Urban Geography, Urban Renewal & Urban Planning', 'Clara'),
    '2025-06-13': ('Tourism & Tourism Management', 'João'),
    '2025-06-20': ('Sustainable Development Goals (SDGs)', 'João and Isabela'),
    '2025-06-27': ('Cultural Geography & Regional Identities', 'João'),
    '2025-07-04': ('Field Work', 'Barbara and Clara'),
    '2025-07-11': ('2 Hours TBD', 'Clara, João, TBD'),
    '2025-07-18': ('2 Hours TBD', 'Isabela, Barbara, TBD')
}

# Inspirational Quotes
quotes = [
    "The only way to do great work is to love what you do. - Steve Jobs",
    "Believe you can and you're halfway there. - Theodore Roosevelt",
    "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
    "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
    "It always seems impossible until it's done. - Nelson Mandela"
]


def days_until_igeo():
    today = datetime.date.today()
    igeo_date = datetime.date(2025, 7, 28)
    return (igeo_date - today).days


def read_todos(filename="todos.txt"):
    """Reads todos from a file and returns them as a string."""
    try:
        with open(filename, "r") as f:
            todos = f.read()
        return todos
    except FileNotFoundError:
        return "No todos.txt file found."
    except Exception as e:
        return f"Error reading todos.txt: {e}"


def send_email(subject, html_body, plain_body):
    msg = MIMEMultipart('alternative')
    msg['From'] = SMTP_USER
    msg['To'] = ', '.join(students)
    msg['Subject'] = subject

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(plain_body, 'plain')
    part2 = MIMEText(html_body, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, students, msg.as_string())
        print("Email sent successfully!")
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
    except Exception as e:
        print(f"General email sending error: {e}")
    finally:
        try:
            server.quit()
        except Exception as e:
            print("Error during server.quit():", e)


def main():
    today = datetime.date.today()
    day_of_week = today.weekday()
    days_until_friday = (4 - day_of_week) % 7
    friday_date = today + datetime.timedelta(days=days_until_friday)
    week_start_str = datetime.date(2025, 3, 21).strftime('%Y-%m-%d')

    if week_start_str in schedule:
        topic, presenter = schedule[week_start_str]
        days_left = days_until_igeo()

        # Get a random quote
        quote = random.choice(quotes)

        # Read todos from file
        todos = read_todos()

        subject = f'Weekly Study Plan: {topic} - {days_left} days until iGeo'

        # HTML Body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
            <p>Dear Students,</p>
            <p>This week we will study "<b>{topic}</b>".</p>
            <p>{presenter} will be presenting on Friday.</p>
            <p>There are {days_left} days left until iGeo (July 28, 2025).</p>
            
            <p>For this week, please focus on the following:</p>
            <pre>{todos}</pre>
            <p><b>Because today is Thursday and you guys have a lot to review from the previous emails, there is nothing new to read from this email. Please remember the following tasks:</b></p>
            <p><b>Tasks for this week:</b></p>
            <ul>
                <li>Study the basic concepts of {topic}.</li>
                <li>Review any relevant notes from previous sessions and the previous emails.</li>
                <li>Prepare any questions you have for {presenter}.</li>
            </ul>
            <p>Have you prepared everything for Friday's presentation and discussion?</p>
            <p>I am here if you need anything.</p>
            <p>Best regards,<br>Your Teamleader Guilherme S.</p>
            <p>Before I go for good I just wanted to remind you of this:</p>
            <p><b>{quote}</b></p>


        </body>
        </html>
        """

        # Plain Text Body (for clients that don't support HTML)
        plain_body = (f'Dear Students,\n\n'
                      f'This week we will study "{topic}".\n'
                      f'{presenter} will be presenting on Friday.\n'
                      f'There are {days_left} days left until iGeo (July 28, 2025).\n\n'
                      f'{quote}\n\n'
                      f'For this week, please focus on the following:\n'
                      f'{todos}\n\n'
                      f'Because today is Thursday and you guys have a lot to review from the previous emails, there is nothing new to read from this email. Please remember the following tasks:\n'
                      f'Tasks for this week:\n'
                      f'- Study the basic concepts of {topic}.\n'
                      f'- Review any relevant notes from previous sessions and the previous emails.\n'
                      f'- Prepare any questions you have for {presenter}.\n\n'
                      f'Have you prepared everything for Friday\'s presentation and discussion?\n\n'
                      f'I am here if you need anything.\n\n'
                      f'Best regards,\nYour Teamleader Guilherme S.')

        send_email(subject, html_body, plain_body)

    else:
        print(f"No topic scheduled for {week_start_str}")


if __name__ == '__main__':
    main()