import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os  # Import the 'os' module
import datetime
import google.generativeai as genai
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter  # Import letter page size
import re

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

# Weekly Schedule
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

# Configure Gemini
GOOGLE_API_KEY = "AIzaSyC9AMs2mVOr94XJfaui8BBWTOWURvFQvxM"
genai.configure(api_key=GOOGLE_API_KEY)


def days_until_igeo():
    today = datetime.date.today()
    igeo_date = datetime.date(2025, 7, 28)
    return (igeo_date - today).days


def setup_genai():
    """Configures and returns the Gemini model."""
    api_key = "AIzaSyC9AMs2mVOr94XJfaui8BBWTOWURvFQvxM"  # Your actual API key
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")  # Adjust the model as needed
    return model


def generate_gemini_summary(model, topic):
    """Generates a summary of a topic using Gemini."""
    prompt = f"Explain the topic of {topic} in a simple and pedagogical way for high school geography students they are going to compete on IGEO2025. Include key concepts, real-world examples, and potential exam questions related to the topic maybe some questions related to real world events. Keep the explanation concise and easy to understand. Aim for around 500 words."
    try:
        response = model.generate_content(prompt)
        if response.text:
            # Clean up the text a bit
            text = response.text.replace("*", "")  # Remove asterisks
            return text
        else:
            return None
    except Exception as e:
        print(f"DEBUG: Error generating Gemini summary: {e}")
        return None


def create_pdf_from_text(text, topic):
    """Creates a PDF from the given text with improved formatting."""
    filename = f"{topic}_summary.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()

    story = []

    # Title Style
    title_style = styles['h1']
    title_style.alignment = 1  # Center align
    story.append(Paragraph(topic, title_style))
    story.append(Spacer(1, 0.2 * inch))

    # Subheading Style
    subheading_style = styles['h2']
    subheading_style.spaceBefore = 0.1 * inch

    # Body Style
    body_style = styles['Normal']
    body_style.fontName = "Helvetica"
    body_style.fontSize = 12
    body_style.leading = 14

    # Split the text into paragraphs based on line breaks
    paragraphs = text.split('\n')

    for paragraph in paragraphs:
        paragraph = paragraph.strip()  # Remove leading/trailing whitespace

        # Skip empty paragraphs
        if not paragraph:
            continue

        # Simplified logic:  Assume Gemini output doesn't need special subheading detection
        story.append(Paragraph(paragraph, body_style))
        story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    return filename


def send_email(subject, body, attachment_path=None):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = ', '.join(students)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment_path:
        try:
            with open(attachment_path, 'rb') as attachment:
                part = MIMEBase('application', "pdf")  # Specific MIME type for PDF
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"')
                msg.attach(part)
        except FileNotFoundError:
            print(f"DEBUG: Attachment file not found: {attachment_path}")
            attachment_path = None  # Ensure it's None to avoid issues
        except Exception as e:
            print(f"DEBUG: Error attaching file: {e}")
            attachment_path = None  # Ensure it's None to avoid issues

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, students, msg.as_string())
        print("DEBUG: Email sent successfully!")
    except smtplib.SMTPAuthenticationError as e:
        print(f"DEBUG: SMTP Authentication Error: {e}")
    except smtplib.SMTPException as e:
        print(f"DEBUG: SMTP Error: {e}")
    except Exception as e:
        print(f"DEBUG: General email sending error: {e}")
    finally:
        try:
            server.quit()
        except Exception as e:
            print("DEBUG: Error during server.quit():", e)


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


def main():
    today = datetime.date.today()
    day_of_week = today.weekday()
    days_until_friday = (4 - day_of_week) % 7
    friday_date = today + datetime.timedelta(days=days_until_friday)
    week_start_str = friday_date.strftime('%Y-%m-%d')

    print(f"DEBUG: week_start_str = {week_start_str}")
    print("DEBUG: Reached IF statement")

    week_start_str = datetime.date(2025, 3, 21).strftime('%Y-%m-%d')  # FORCE to 2025-03-21

    if week_start_str in schedule:
        topic, presenter = schedule[week_start_str]
        days_left = days_until_igeo()

        gemini_model = setup_genai()  # Initialize Gemini model
        gemini_summary = generate_gemini_summary(gemini_model, topic)  # Generate summary

        if gemini_summary:
            article_path = create_pdf_from_text(gemini_summary, topic)  # Create PDF with Gemini formatting
            print(f"DEBUG: Attachment path: {article_path}")
        else:
            article_path = None
            print("DEBUG: Failed to generate Gemini summary.")

        # Read todos from file
        todos = read_todos()

        if article_path:
            subject = f'Weekly Study Plan: {topic} - {days_left} days until iGeo'
            body = (f'Dear Students,\n\n'
                    f'This week we will study "{topic}".\n'
                    f'{presenter} will present on Friday.\n'
                    f'There are {days_left} days left until iGeo (July 28, 2025).\n\n'
                    f'As you guys know today is Monday so here are the explanations for this week\'s topic.\n\n'
                    f'Following this attached is a summary of this week\'s topic generated by Gemini.\n\n'
                    f'**Important Notes for this Week:**\n'
                    f'{todos}\n\n'
                    f'Best regards,\nYour Teamleader Guilherme S.')
            send_email(subject, body, article_path)
        else:
            subject = f'Weekly Study Plan: {topic} - [Article Failed]'
            body = (f'Dear Students,\n\n'
                    f'This week we will study "{topic}".\n'
                    f'{presenter} will present on Friday.\n\n'
                    f'There are {days_left} days left until iGeo (July 28, 2025).\n\n'
                    f'Unfortunately, the article summary could not be retrieved this week.\n\n'
                    f'**Important Notes for this Week:**\n'
                    f'{todos}\n\n'
                    f'Best regards,\nYour Teamleader Guilherme')
            send_email(subject, body, None)

    else:
        print(f"DEBUG: No topic scheduled for {week_start_str}")


if __name__ == '__main__':
    main()