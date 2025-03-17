import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os  # Import the 'os' module
import datetime
import requests  # Import requests even though it's not directly used now, to avoid "not found" message
from bs4 import BeautifulSoup
import json
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from reportlab.pdfgen import canvas  # Import for PDF generation
from reportlab.lib.pagesizes import letter
from googlesearch import search
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors


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


def days_until_igeo():
    today = datetime.date.today()
    igeo_date = datetime.date(2025, 7, 28)
    return (igeo_date - today).days


def fetch_article_summary(topic):
    """Fetches an article summary using the googlesearch-python library and saves it as a PDF."""
    try:
        search_query = f"Geographical articles on: {topic}"  # Search on Google - Combined search
        print(f"DEBUG: Searching Google for: {search_query}")

        # Use googlesearch library to get multiple results
        results = search(search_query, num_results=5, lang="en", region="com")  # Increase to 5 results

        summaries = []
        article_urls = []

        for article_url in results:
            if not article_url:  # Check if article_url is empty
                print("DEBUG: Empty article URL returned by Google Search.")
                continue  # Try the next result

            # Targeted filter to ONLY skip Google search pages (or similar)
            if "google.com" in article_url or "google.com.br" in article_url or "/search?" in article_url:  # Improved filter
                print(f"DEBUG: Skipping Google-related URL: {article_url}")
                continue


            print(f"DEBUG: Trying URL: {article_url}")
            article_urls.append(article_url)

            # Fetch the content of the article page
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }

                #Retry settings (to retry the connection in case of failure)
                session = requests.Session()
                retry = Retry(total=3,
                              backoff_factor=0.5,
                              status_forcelist=[403, 500, 502, 503, 504])
                adapter = HTTPAdapter(max_retries=retry)
                session.mount('http://', adapter)
                session.mount('https://', adapter)

                article_response = session.get(article_url, headers=headers)
                article_response.raise_for_status()

                article_soup = BeautifulSoup(article_response.content, 'html.parser')

                if article_soup is None:  # Check if BeautifulSoup failed
                    print("DEBUG: BeautifulSoup failed to parse the article content.")
                    summaries.append(f"Could not retrieve summary from {article_url} - BeautifulSoup parsing failed.")
                    continue

                # Extract the article summary from meta description and first paragraphs
                summary = ""
                meta_description = article_soup.find("meta", attrs={"name": "description"})
                if meta_description and meta_description.get("content"):
                    summary = meta_description["content"]
                    print(f"DEBUG: Found summary from meta description")

                # If meta description is not available or too short, use the first paragraph(s)
                if not summary or len(summary) < 50:  # Check if summary is too short
                    paragraphs = article_soup.find_all('p')
                    summary_paragraphs = []
                    for para in paragraphs[:3]:  # Smaller summary for each article
                        try:
                            text = para.get_text(strip=True)  # strip whitespace
                            if text:  # Only add if not empty
                                summary_paragraphs.append(text)
                        except Exception as e:
                            print(f"DEBUG: Error getting text from paragraph: {e}")

                    paragraph_summary = '\n'.join(summary_paragraphs)
                    if paragraph_summary:
                        summary = paragraph_summary
                        print(f"DEBUG: Found summary from first paragraphs")
                    else:
                        print("DEBUG: No suitable paragraphs found for summary.")
                        summaries.append(f"Could not extract summary from {article_url} - No meta description or paragraphs found.")
                        continue  # Skip to next URL if no summary can be extracted

                print(f"DEBUG: Article Summary for {article_url}:\n{summary}")
                summaries.append(summary)

            except requests.exceptions.RequestException as e:
                print(f"DEBUG: Request Exception for {article_url}: {e}")
                summaries.append(f"Could not retrieve content from {article_url} - Request Exception: {e}")  # More detailed fallback
            except Exception as e:
                print(f"DEBUG: General Exception for {article_url}: {e}")
                summaries.append(f"Could not retrieve content from {article_url} - General Exception: {e}") # More detailed fallback

        if not summaries:
            print("DEBUG: No valid article summaries available.")
            return None

        file_path = f'{topic}_combined_summary.pdf'
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        styleN = styles["Normal"]
        styleN.fontName = "Helvetica"
        styleN.fontSize = 10
        styleN.leading = 12

        # Add a style for links
        styleA = styles["Normal"]
        styleA.fontName = "Helvetica"
        styleA.fontSize = 10
        styleA.leading = 12
        styleA.textColor = colors.blue
        styleA.underline = 1

        story = []
        for i, summary in enumerate(summaries):
            story.append(Paragraph(f"<b>Article {i+1}:</b>", styles["Normal"]))  # Article Number
            story.append(Paragraph(summary, styleN))

            # Create a ReportLab-compatible link (encode the URL)
            encoded_url = urllib.parse.quote(article_urls[i], safe=":/") #Properly encode the URL
            link_text = f'<a href="{encoded_url}">{article_urls[i]}</a>'
            story.append(Paragraph(f"<b>Source:</b> {link_text}", styleA)) # use the new style

            story.append(Spacer(1, 0.2*inch))  # Space between articles (using Spacer)

        doc.build(story)
        return file_path

    except Exception as e:
        print(f"DEBUG: Error during Google search processing: {e}")
        return None


def send_email(subject, body, attachment_path=None):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = ', '.join(students)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment_path:
        try:
            # Check if the file exists
            if not os.path.exists(attachment_path):
                print(f"DEBUG: Attachment file not found: {attachment_path}")
                attachment_path = None  # Ensure it's None to avoid later issues
            else:
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', "pdf")  # Specific MIME type for PDF
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)  # Encode the attachment
                    part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"')  # Add filename
                    msg.attach(part)
        except FileNotFoundError:
            print(f"DEBUG: Attachment file not found: {attachment_path}")
            attachment_path = None  # Ensure it's None to avoid later issues
        except Exception as e:
            print(f"DEBUG: Error attaching file: {e}")
            attachment_path = None  # Ensure it's None to avoid later issues

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, students, msg.as_string())
        print("DEBUG: Email sent successfully!")
    except smtplib.SMTPAuthenticationError as e:  # More specific exception
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

        article_path = None  # Initialize article_path to None
        subject = ""  # Initialize subject
        body = ""  # Initialize body
        article_path = fetch_article_summary(topic)

        print(f"DEBUG: Attachment path: {article_path}")  # Add this line

        # Read todos from file
        todos = read_todos()

        if article_path:
            subject = f'Weekly Study Plan: {topic} - {days_left} days until iGeo'
            body = (f'Dear Students,\n\n'
                    f'This week we will study "{topic}".\n'
                    f'{presenter} will present on Friday.\n'
                    f'There are {days_left} days left until iGeo (July 28, 2025).\n\n'
                    f'As you guys know today is Tuesday so here are the cientifical articles for this week\'s topic.\n\n'
                    f'Following this attached is a summary of this week\'s topic.\n\n'
                    f'**Important Notes for this Week:**\n'
                    f'{todos}\n\n'
                    f'Best regards,\nYour Teamleader Guilherme S.')

            send_email(subject, body, article_path)
        else:
            print("DEBUG: No article summary available. Email not sent.")
            subject = f'Weekly Study Plan: {topic} - [Article Failed]'
            body = (f'Dear Students,\n\n'
                    f'This week we will study "{topic}".\n'
                    f'{presenter} will present on Friday.\n\n'
                    f'Unfortunately, the article summary could not be retrieved this week.\n\n'
                    f'**Important Notes for this Week:**\n'
                    f'{todos}\n\n'
                    f'Best regards,\nYour Teamleader Guilherme')
            send_email(subject, body, None) # Send email even if no attachment

    else:
        print(f"DEBUG: No topic scheduled for {week_start_str}")


if __name__ == '__main__':
    main()