import os
import sys
from datetime import datetime, timedelta
import schedule
import logging
import shutil
import subprocess
import time
import signal
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random

# Check if the platform is Windows
if os.name != 'nt':
    import fcntl  # Import fcntl for file locking (Linux/Unix)
else:
    # Define a dummy fcntl for Windows
    class DummyFcntl:
        def flock(self, fd, operation):
            pass  # Do nothing
        def LOCK_EX(self):
            return 0  # Placeholder
        def LOCK_UN(self):
            return 0  # Placeholder
        def LOCK_NB(self):
            return 0

    fcntl = DummyFcntl()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File paths
FILE_PATH = "sent_log.txt"
GERMAN_WORDS_FILE = "ordersentence_database.txt"  # Renamed for clarity
LOG_FILE = "gender_words_log.txt"  # Renamed for clarity
ANKI_DECK_NAME = "DERDIEDAS"  # Base name, date will be appended


# Email configuration
FROM_EMAIL = "example@email.com"  # Using the provided example
TO_EMAIL = "example@email.com"  # Using the provided example
APP_PASSWORD = "keymodel"  # Using the provided example


# Global dictionary to store process information and last run times
script_processes = {}
last_run_times = {}


def read_german_words(file_path):
    """Reads German words and genders from the specified file."""
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:  # Use utf-8-sig to handle BOM
            words = []
            for line in f:
                line = line.strip()  # Remove any surrounding whitespace
                if line:  # Skip empty lines
                    parts = line.split(",")
                    if len(parts) >= 2:  # Ensure there are at least two parts (word and gender)
                        word, gender = parts[:2]  # Only take the first two parts (ignore extra columns)
                        words.append((word.strip(), gender.strip()))  # Strip extra spaces
                    else:
                        logging.warning(f"Skipping invalid line: {line}")
            return words
    except FileNotFoundError:
        logging.error(f"Error: File not found: {file_path}")
        return []
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return []


def read_used_words(file_path):
    """Reads the log file to get previously used words."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f]
    except FileNotFoundError:
        return []

def select_random_words(words, used_words, num_words=5):
    """Selects random German words that haven't been used before."""
    available_words = [word for word in words if word[0] not in used_words]
    if len(available_words) < num_words:
        logging.warning("Warning: Not enough new words available.  Reusing some words.")
        available_words = words  # Reuse words if necessary, but still shuffle
    random.shuffle(available_words)

    selected_words = available_words[:num_words] # Handle cases where fewer than 5 words are available
    return selected_words

def log_used_words(file_path, words):
    """Logs the used German words to the log file."""
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            for word, _ in words:
                f.write(f"{word}\n")
    except Exception as e:
        logging.error(f"Error writing to log file: {e}")

def create_email_content(words):
    """Creates the content for the email."""
    content = "Here are your 5 German words for today:\n\n"
    for word, gender in words:
        content += f"{word} - {gender}\n"  # Corrected display format
    content += "\nLearn them well!"
    return content

def send_email(subject, content, to_email, from_email, app_password):
    """Sends the email."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, app_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Email sending failed: {e}")

def get_last_n_words(file_path, n=35):
    """Gets the last N words from the log file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_n_lines = lines[-n:]
            return [line.strip() for line in last_n_lines]
    except FileNotFoundError:
        logging.error(f"Log file not found: {file_path}")
        return []
    except Exception as e:
        logging.error(f"Error reading log file: {e}")
        return []

def create_anki_deck(words, deck_name):
    """Creates a CSV file suitable for Anki import."""
    csv_file = f"{deck_name}.csv"
    try:
        with open(csv_file, 'w', encoding='utf-8') as f:
            for word in words:
               #Find the gender of the word
               gender = ""
               for w, g in read_german_words(GERMAN_WORDS_FILE):
                   if w == word:
                       gender = g
                       break
               if gender:
                   f.write(f"{word};{gender}\n")
               else:
                   f.write(f"{word};Unknown Gender\n") #Default to unknown if gender not found
        logging.info(f"Anki deck CSV created: {csv_file}")
        return csv_file
    except Exception as e:
        logging.error(f"Error creating Anki deck CSV: {e}")
        return None

def import_anki_deck(csv_file):
    """Imports the Anki deck using AnkiConnect."""
    try:
        import requests
        import json
        # AnkiConnect API endpoint
        url = 'http://127.0.0.1:8765'  # Default AnkiConnect address

        # Define the action to import a deck from a CSV file
        params = {
            "action": "importFile",
            "version": 6,
            "params": {
                "path": os.path.abspath(csv_file),
            }
        }

        # Send the request to AnkiConnect
        response = requests.post(url, data=json.dumps(params))
        response_data = response.json()
        if 'error' in response_data and response_data['error'] is not None:
            logging.error(f"AnkiConnect import error: {response_data['error']}")
        else:
            logging.info(f"Anki deck imported successfully using AnkiConnect.")
            #os.remove(csv_file)  # Optionally remove the CSV file after import
    except ImportError:
        logging.error("Error: 'requests' library not found.  Please install it (pip install requests).")
    except requests.exceptions.ConnectionError:
        logging.error("Error: Could not connect to AnkiConnect.  Make sure Anki is running with AnkiConnect installed.")
    except Exception as e:
        logging.error(f"Error importing Anki deck: {e}")


def create_anki_cards():
    """Creates Anki cards from the last N words in the log."""
    today = datetime.now().strftime("%Y-%m-%d")
    deck_name = f"{ANKI_DECK_NAME} {today}"
    last_words = get_last_n_words(LOG_FILE, 35)
    if last_words:
        anki_csv_file = create_anki_deck(last_words, deck_name)
        if anki_csv_file:
            import_anki_deck(anki_csv_file)
    else:
        logging.warning("No words found in the log to create Anki cards.")


def daily_word_email():
    """Sends the daily word email."""
    german_words = read_german_words(GERMAN_WORDS_FILE)
    used_words = read_used_words(LOG_FILE)

    if not german_words:
        logging.error("No German words found.  Exiting.")
        return

    words_to_send = select_random_words(german_words, used_words)

    if not words_to_send:
        logging.warning("No new words available. Exiting.")
        return

    email_content = create_email_content(words_to_send)
    email_subject = "Your Daily German Words"

    send_email(email_subject, email_content, TO_EMAIL, FROM_EMAIL, APP_PASSWORD)
    log_used_words(LOG_FILE, words_to_send)


def send_whatsapp_message(file_path):
    """Sends a WhatsApp message using a Linux CLI tool."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        if not content:
            logging.warning("The file is empty. Please check the content.")
            return

        logging.info(f"File content read successfully: {content}")

        # Replace with your actual WhatsApp sending command (e.g., using yowsup-cli)
        phone_number = "+1234567890"  # Replace with recipient's phone number
        command = f"echo '{content}' | mail -s 'WhatsApp Message' {phone_number}@txt.att.net"  # Replace with yowsup or other command

        logging.info(f"Executing command: {command}")  # Log the exact command being executed
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        # Do not call process.communicate() here

        logging.info(f"Started sending WhatsApp message in the background to {phone_number} (PID: {process.pid})")

    except FileNotFoundError:
        logging.error(f"Error: File '{file_path}' not found.")
    except Exception as e:
        logging.exception(f"An error occurred: {e}")


def reset_sent_log(file_path):
    """Resets the sent_log.txt file to its default content."""
    try:
        default_content = (
            "Main: *NOT*\n"
            "Carsten: *NOT* MWF \n"
            "Brendan: *NOT* MWF \n"
            "keith: *NOT* MWF \n"
            "Sean: *NOT* \n"
            "Giuseppe: *NOT*\n"
            "Ron: *NOT* \n"
            "Christine: *NOT* \n"
            "Michael: *NOT*  \n"
            "Patrick: *NOT* \n"
            "Luis: *NOT* FS \n"
            "Amanda: *NOT*  \n"
            "Josh: *NOT* MWF \n"
            "Anton: *NOT* MWF \n"
            "Gaetan: *NOT* TTS \n"
            "Viviana: *NOT* MWF \n"
        )

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(default_content)
        logging.info(f"Datei '{file_path}' erfolgreich zurückgesetzt.")
    except Exception as e:
        logging.exception(f"Fehler beim Zurücksetzen der Datei: {e}")


def run_script(script_name):
    """Runs a Python script, using file locking to ensure single execution."""
    lock_file_path = f"/tmp/{script_name.replace('.py', '')}.lock"  # Create a lock file per script.  Important!
    logging.debug(f"Lock file path for {script_name}: {lock_file_path}")

    try:
        lock_file = open(lock_file_path, "w")
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # Non-blocking exclusive lock
            logging.info(f"Acquired lock for {script_name}")

            logging.info(f"Starting script: {script_name} in background")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, script_name)
            logging.info(f"Executing script: {script_path}")
            process = subprocess.Popen(['python3', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       close_fds=True)
            logging.info(f"Started {script_name} in background (PID: {process.pid})")
            script_processes[script_name] = {'process': process, 'last_run': datetime.now()}
            last_run_times[script_name] = datetime.now()

        except OSError as e:
            if e.errno == 11:  #errno.EAGAIN Resource temporarily unavailable
                logging.warning(f"Skipping {script_name} because it's already running (lock held).")
            else:
                logging.error(f"Error locking {script_name}: {e}")
        finally:
            if 'lock_file' in locals(): # Release the lock
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                logging.info(f"Released lock for {script_name}")

    except Exception as e:
        logging.exception(f"Error running {script_name}: {e}")


def run_amanda():
    logging.info("run_amanda() function called")
    run_script('amanda.py')


def run_myscripts():
    run_script('ai-automated.py')
    run_script('Flashcards.py')
    run_script('expressions.py')
    run_script('phraseorder.py')
    run_script('russian.py')
    run_script('italian.py')
    run_script('italianbella.py')


def run_ai_carsten():
    run_script('ai-carsten.py')


def run_brendan():
    run_script('brendan.py')


def run_keith():
    run_script('keith.py')


def run_sean():
    run_script('sean.py')


def run_seanfun():
    print('')


def run_giuseppe():
    run_script('giuseppe.py')
    run_script('Flashcardssean.py')
    run_script('Flashcardsbrendan.py')


def run_ron():
    run_script('ron.py')


def run_chr():
    run_script('christine.py')


def run_mch():
    run_script('michael.py')


def run_patrick():
    run_script('patrick.py')
    run_script('phraseorderpatrick.py')


def run_luis():
    run_script('luis.py')


def run_josh():
    run_script('josh.py')


def run_anton():

    run_script('viviana.py')
    run_script('robert.py')


def run_gae():
    run_script('gaetan.py')
    run_script('patricken.py')
    run_script('Caio.py')

def run_caioderdiedas():
    run_script('caioderdiedas.py')


def run_igeo_monday():
    run_script('igeomonday.py')

def run_igeo_tuesday():
    run_script('igeotuesday.py')

def run_igeo_wednesday():
    run_script('igeowednesday.py')

def run_igeo_thursday():
    run_script('igeothursday.py')

def run_igeo_friday():
    run_script('igeofriday.py')

def run_igeo_saturday():
    run_script('igeosaturday.py')



def should_run_today(script_tag, allowed_days):
    """Checks if the script should run today based on allowed days."""
    now = datetime.now()
    weekday = now.weekday()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    logging.info(
        f"Checking if {script_tag} should run today. Day: {day_names[weekday]} ({weekday}), Allowed Days: {allowed_days}")
    return weekday in allowed_days


def run_if_allowed(script_tag, func, allowed_days):
    """Runs a function if the current day is in the allowed days."""
    if should_run_today(script_tag, allowed_days):
        logging.info(f"Running {script_tag} because today is allowed.")
        func()
    else:
        logging.info(f"Skipping {script_tag} today.")


def next_valid_run_datetime(allowed_days, time_of_day):
    """Calculates the next valid datetime for a script to run."""
    now = datetime.now()
    target_time = datetime.strptime(time_of_day, "%H:%M").time()
    next_run_time = datetime.combine(now.date(), target_time)

    while next_run_time <= now or next_run_time.weekday() not in allowed_days:
        next_run_time += timedelta(days=1)

    return next_run_time


def time_until_next_run(script_tag, time_of_day):
    """Calculates the time until the next scheduled run of a script."""
    try:
        next_run = next_valid_run_datetime(allowed_days[script_tag], time_of_day)
        return next_run - datetime.now()
    except Exception as e:
        logging.error(f"Error calculating next run time for {script_tag}: {e}")
        return None


def get_terminal_width():
    """Gets the terminal width."""
    return shutil.get_terminal_size().columns


def get_terminal_height():
    """Gets the terminal height."""
    return shutil.get_terminal_size().lines


def display_smoothly(lines):
    """Displays content smoothly on the terminal."""
    os.system('clear')  # Clear the console


def get_current_status():
    """Formats and returns the current status string."""
    times = {
        'Main': time_until_next_run('myscripts', "06:00"),
        'Carsten': time_until_next_run('student', "02:04"),
        'Keith': time_until_next_run('keith', "08:01"),
        'Sean': time_until_next_run('sean', "08:02"),
        'Seanfun': time_until_next_run('seanfun', "08:02"),
        'Brendan': time_until_next_run('brendan', "11:03"),
        'Giuseppe': time_until_next_run('giuseppe', "04:05"),
        'Ron': time_until_next_run('ron', "02:05"),
        'Christine': time_until_next_run('chr', "11:05"),
        'Michael': time_until_next_run('mch', "11:09"),
        'Patrick': time_until_next_run('patrick', "20:06"),
        'Luis': time_until_next_run('luis', "08:06"),
        'Amanda': time_until_next_run('amanda', "13:25"),
        'Josh': time_until_next_run('josh', "10:06"),
        'Anton, Viviana e Robert': time_until_next_run('anton', "06:04"),
        'Gaetan , Patricken e Caio': time_until_next_run('gae', "03:02"),
        'CaioDerDieDas': time_until_next_run('caioderdiedas', "03:02"),
        'iGeo Monday': time_until_next_run('igeomonday', "06:00"),  # Add iGeo to status
        'iGeo Tuesday': time_until_next_run('igeotuesday', "06:00"),  # Add iGeo to status
        'iGeo Wednesday': time_until_next_run('igeowednesday', "06:00"),  # Add iGeo to status
        'iGeo Thursday': time_until_next_run('igeothursday', "06:00"),  # Add iGeo to status
        'iGeo Friday': time_until_next_run('igeofriday', "06:00"),  # Add iGeo to status
        'iGeo Saturday': time_until_next_run('igeosaturday', "13:54"),  # Add iGeo to status

    }

    prompt = "\n".join(
        f"{key}: {str(value).split('.')[0] if value else 'No Schedule'}"
        for key, value in times.items()
    )

    return prompt.split("\n")


# Specify allowed days for each script (0 = Monday, 6 = Sunday)
allowed_days = {
    'myscripts': [0, 1, 2, 3, 4, 5, 6],
    'student': [0, 2, 4],
    'brendan': [0, 2, 4],
    'keith': [0, 2, 4],
    'sean': [0, 2,1,4, 3],
    'seanfun': [1, 4],
    'giuseppe': [0, 1, 2, 3, 4],
    'ron': [0, 1, 2, 3, 4],
    'chr': [0, 1, 2, 3, 4],
    'mch': [0, 1, 2, 3, 4],
    'patrick': [0, 1, 2, 3, 4],
    'luis': [4, 5],
    'amanda': [0, 1, 2, 3, 4],
    'josh': [0, 2, 5],
    'anton': [6, 2, 4],
    'gae': [1, 3, 5],
    'caioderdiedas': [1,2, 3,4, 5],
    'igeomonday': [1],  # Monday
    'igeotuesday': [2],  # Tuesday
    'igeowednesday': [3],  # Wednesday
    'igeothursday': [4],  # Thursday
    'igeofriday': [5],  # Friday
    'igeosaturday': [6],  # Saturday


}

# Schedule jobs with specific allowed days
schedule.every().day.at("06:00").do(run_if_allowed, 'myscripts', run_myscripts, allowed_days['myscripts'])
schedule.every().day.at("13:04").do(run_if_allowed, 'student', run_ai_carsten, allowed_days['student'])
schedule.every().day.at("08:01").do(run_if_allowed, 'keith', run_keith, allowed_days['keith'])
schedule.every().day.at("08:02").do(run_if_allowed, 'sean', run_sean, allowed_days['sean'])
schedule.every().day.at("08:02").do(run_if_allowed, 'seanfun', run_seanfun, allowed_days['seanfun'])
schedule.every().day.at("11:03").do(run_if_allowed, 'brendan', run_brendan, allowed_days['brendan'])
schedule.every().day.at("04:05").do(run_if_allowed, 'giuseppe', run_giuseppe, allowed_days['giuseppe'])
schedule.every().day.at("02:05").do(run_if_allowed, 'ron', run_ron, allowed_days['ron'])
schedule.every().day.at("11:05").do(run_if_allowed, 'chr', run_chr, allowed_days['chr'])
schedule.every().day.at("11:09").do(run_if_allowed, 'mch', run_mch, allowed_days['mch'])
schedule.every().day.at("20:06").do(run_if_allowed, 'patrick', run_patrick, allowed_days['patrick'])
schedule.every().day.at("08:06").do(run_if_allowed, 'luis', run_luis, allowed_days['luis'])
schedule.every().day.at("13:25").do(run_if_allowed, 'amanda', run_amanda, allowed_days['amanda'])
schedule.every().day.at("10:06").do(run_if_allowed, 'josh', run_josh, allowed_days['josh'])
schedule.every().day.at("06:04").do(run_if_allowed, 'anton', run_anton, allowed_days['anton'])
schedule.every().day.at("03:02").do(run_if_allowed, 'gae', run_gae, allowed_days['gae'])
schedule.every().day.at("03:02").do(run_if_allowed, 'caioderdiedas', run_gae, allowed_days['caioderdiedas'])

schedule.every().day.at("23:51").do(reset_sent_log, FILE_PATH)
schedule.every().day.at("20:20").do(send_whatsapp_message, FILE_PATH)
schedule.every().day.at("12:30").do(send_whatsapp_message, FILE_PATH)


# Schedule daily word email
schedule.every().day.at("08:00").do(daily_word_email)

# Schedule Anki card creation every Monday at 2:30 PM
schedule.every().monday.at("14:30").do(create_anki_cards) #24-hour format


# iGeo scheduling
schedule.every().monday.at("06:00").do(run_if_allowed, 'igeomonday', run_igeo_monday, allowed_days['igeomonday'])
schedule.every().tuesday.at("06:00").do(run_if_allowed, 'igeotuesday', run_igeo_tuesday, allowed_days['igeotuesday'])
schedule.every().wednesday.at("06:00").do(run_if_allowed, 'igeowednesday', run_igeo_wednesday, allowed_days['igeowednesday'])
schedule.every().thursday.at("06:00").do(run_if_allowed, 'igeothursday', run_igeo_thursday, allowed_days['igeothursday'])
schedule.every().friday.at("06:00").do(run_if_allowed, 'igeofriday', run_igeo_friday, allowed_days['igeofriday'])
schedule.every().saturday.at("13:54").do(run_if_allowed, 'igeosaturday', run_igeo_saturday, allowed_days['igeosaturday'])





# Main loop
if __name__ == "__main__":
    try:
        while True:
            logging.debug(f"Running schedule.get_jobs(): {schedule.get_jobs()}")
            schedule.run_pending()
            status_lines = get_current_status()  # Get the status lines

            display_smoothly([])  # clear
            print('\n'.join(status_lines))  # Printing status lines

            time.sleep(2)
    except KeyboardInterrupt:
        logging.info("Program terminated by user.")

        # Terminate any running scripts upon exit (less important now, but still good practice)
        for script_name, process_data in script_processes.items():
            process = process_data['process']
            if process.poll() is None:  # Still running
                logging.info(f"Terminating {script_name} (PID: {process.pid})")
                try:
                    os.kill(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logging.warning(f"Forcefully killing {script_name} (PID: {process.pid})")
                    os.kill(process.pid, signal.SIGKILL)
                except Exception as e:
                    logging.error(f"Error terminating {script_name}: {e}")

        sys.exit(0)

    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)







