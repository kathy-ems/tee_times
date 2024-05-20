import sys
from random import randint
from typing import Tuple
from time import sleep
from datetime import date, time, datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
from joblib import Parallel, delayed
from selenium.webdriver.common.by import By
import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

load_dotenv()
HOST_NAME = os.environ.get("HOST_NAME")


# Set up the email parameters
EMAIL_ADDRESS = os.environ.get("EMAIL")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
sender_email = EMAIL_ADDRESS
recipient_email = EMAIL_ADDRESS

# create the email message object
msg = EmailMessage()
msg["From"] = sender_email
msg["To"] = recipient_email
msg["Subject"] = "Booking a Tee Time"

server = smtplib.SMTP("smtp.gmail.com", 587)
server.ehlo()
server.starttls()
server.ehlo()
server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
print("Logged into SMTP successfully")


def logError(message) -> None:
    global errorMessage
    errorMressage = f"{errorMessage}; {message}"
    return errorMessage


def sendEmailMessage(subject, message) -> None:
    del msg["subject"]
    msg["Subject"] = f"{subject} ({HOST_NAME})"
    msg.set_content(message)
    server.send_message(msg)


############################################################################################
# Be Sure to set all these params prior to running application                            #
############################################################################################
# begin_time = time(18,59,55) # example

begin_time = time(1, 0)  # When should it start reserving a tee time
end_time = time(23, 7, 0)  # When should it stop trying to get a tee time
max_try = 2  # change back to 500 when working
is_current_month = True  # False when reservation_day is for next month
is_previous_month = False  # True when reservation happens at the end of the month and needs to be moved back a month
desired_tee_time = "08:27 AM"  # tee time in this format 'hh:mm AM'
course_number = int(3)  # course No; cradle is 10
book_first_avail = True  # True books the first available tee time on this course
num_of_players = int(2)  # Only allows 1-2 players at the moment
is_testing_mode = (
    True  # True will not book the round & will show browser window (not be headless)
)
reservation_day = int(12)  # day of current month to book
auto_select_date_based_on_course = (
    False  # True sets the days out for booking window based on course
)
random_signature_course = False  # True randomly chooses course No 7-9
afternoon_round = (
    True  # True picks tee time automatically in the afternoon for No 2, No 4
)
############################################################################################

if len(sys.argv) >= 2:  # Only run the below if there are args
    course_number = int(sys.argv[1]) if len(sys.argv) >= 2 else course_number  # int
    is_testing_mode = (
        False if len(sys.argv) >= 3 and sys.argv[2] == "False" else True
    )  # bool
    book_first_avail = (
        False if len(sys.argv) >= 4 and sys.argv[3] == "False" else True
    )  # bool
    auto_select_date_based_on_course = (
        False if len(sys.argv) >= 5 and sys.argv[4] == "False" else True
    )  # bool
    num_of_players = int(sys.argv[5]) if len(sys.argv) >= 6 else num_of_players  # int
    random_signature_course = (
        True if len(sys.argv) >= 7 and sys.argv[6] == "True" else False
    )  # bool
    afternoon_round = (
        True if len(sys.argv) >= 8 and sys.argv[7] == "True" else False
    )  # bool

if random_signature_course == True and course_number in [7, 8, 9]:
    # course_number = randint(7, 9)
    max_try = 3
if afternoon_round == True:
    desired_tee_time = "02:"

bot_start_time = datetime.now()
bot_stop_time = datetime.now()

course_booking_days_out = {
    1: 8,
    2: 8,
    3: 8,
    4: 8,
    5: 8,
    6: 8,
    7: 11,
    8: 11,
    9: 11,
    10: 2,
}

course_booking_days_out_when_false = {
    1: 7,
    2: 7,
    3: 7,
    4: 7,
    5: 7,
    6: 7,
    7: 10,
    8: 10,
    9: 10,
    10: 1,
}
timezone = "testing"

if is_testing_mode == True:
    ## TESTING TIMES ##
    begin_time = time(0, 59, 40)
    begin_time2 = time(0, 59, 39)
    begin_time3 = time(0, 59, 38)
    end_time = time(23, 59, 59)

    # begin_time = time(21, 51, 40)
    # begin_time2 = time(21, 51, 39)
    # begin_time3 = time(21, 51, 38)
    # end_time = time(22, 7)


if is_testing_mode == False:
    ## EASTERN ##
    begin_time = time(22, 00, 00)
    begin_time2 = time(21, 59, 59)
    begin_time3 = time(21, 59, 58)
    end_time = time(22, 7)
    timezone = "eastern"

    if HOST_NAME == "Work_computer":
        ## Pacific ##
        begin_time = time(19, 00, 00)
        begin_time2 = time(18, 59, 59)
        begin_time3 = time(18, 59, 58)
        end_time = time(19, 7)
        timezone = "pacific"

print(f"Timezone: {timezone}")

# Defaults to 10, 7, 1 days out based on course
if auto_select_date_based_on_course:
    today = date.today()
    print(today)
    if is_testing_mode == False:
        days_out = course_booking_days_out[course_number]
    else:
        days_out = course_booking_days_out_when_false[course_number]
    future_date = today + timedelta(days=days_out)
    reservation_day = future_date.day
    default_end_date = today + timedelta(days=5)

    if today.month != future_date.month:
        is_current_month = False

    if today.day > default_end_date.day:
        is_previous_month = True


def elapsed_time(message) -> None:
    bot_stop_time = datetime.now()
    delta = bot_stop_time - bot_start_time
    seconds = delta.total_seconds()
    print(f"{message} in {seconds} seconds")


def check_current_time() -> Tuple[time, bool]:
    """
    Check current time is between 22:00 and 22:07.
    Returns current time and if it is between begin and end time.
    """
    dt_now = datetime.now()
    current_time = time(dt_now.hour, dt_now.minute, dt_now.second)
    return current_time, (begin_time <= current_time) and (current_time < end_time)


def checkForErrorPopUp(driver) -> bool:
    wait = WebDriverWait(driver, 6)
    overlayErrorMessage = wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "cdk-global-overlay-wrapper"))
    )
    if overlayErrorMessage:
        overlay_popup_error = True
        if is_testing_mode == False:
            sendEmailMessage(
                "Unable to book tee time",
                f"Overlay popup error when trying to book on course {course_number}. ",
            )
            # logError("No slots")
        else:
            print(f"Overlay popup error on course {course_number}")
        return True
    else:
        print("no error message")
        return False


## SELECT SLOT BY FIRST AVAILABLE TEE TIME
def select_slot_by_first_available(driver) -> bool:
    try:
        ## obtain all open slots and find desired slot
        allAvlSlots = driver.find_elements(
            By.CLASS_NAME, "available-slot:not(.booked-slot)"
        )
        for slot in allAvlSlots:
            try:
                chips = slot.find_elements(By.CLASS_NAME, "player-chip-detail")
                available_spots = 4 - len(chips)
                if available_spots >= num_of_players:
                    ## Click BOOK in the target slot
                    slot.find_element(By.CLASS_NAME, "submit-button").click()
                    sleep(1)
                    ## selects number of players from drop down
                    guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
                    player_options = guestPane.find_elements(By.TAG_NAME, "li")
                    player_options[num_of_players - 1].click()
                    return True
            except Exception as e:
                try:
                    sleep(30)
                except Exception as e:
                    print(f"Select players for first available had an error: {e}")
                    return False
        else:
            return False
    except Exception as e:
        print(f"Checking first available tee time error {e}")
        return False


## SELECT SLOT BY TEE TIME
def select_slot_by_tee_time(driver) -> None:
    try:
        slotIndex = int(0)
        ## obtain all open slots and find desired slot
        allAvlSlots = driver.find_elements(
            By.CLASS_NAME, "available-slot:not(.booked-slot)"
        )
        for i, slot in enumerate(allAvlSlots):
            ## GET BY TEE TIME
            try:
                div = slot.find_element(By.CLASS_NAME, "schedule-time")
                if div.text == desired_tee_time:
                    ## store slot index of desired slot number
                    slotIndex = i
                    print(f"The tee time {div.text} was found at index {i}")
                    break
            except Exception as e:
                print(f"First available tee time error {e}")
                return False
        else:
            print(f"The available tee time was not found")

        ## Click BOOK in the target slot
        allAvlSlots[slotIndex].find_element(By.CLASS_NAME, "submit-button").click()
        sleep(0.5)  # Wait for players window to open
        ## selects number of players
        guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
        player_options = guestPane.find_elements(By.TAG_NAME, "li")
        player_options[num_of_players - 1].click()
        return None
    except Exception as e:
        print("Waiting extra time for players to load")
        try:
            sleep(0.5)  # Wait for players window to open
            ## selects number of players
            guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
            player_options = guestPane.find_elements(By.TAG_NAME, "li")
            player_options[num_of_players - 1].click()
            return None
        except Exception as e:
            print(f"select players had an error: {e}")
            return False


## SELECT AFTERNOON TEE TIME
def select_afternoon_tee_time(driver) -> None:
    try:
        ## obtain all open slots and find desired slot
        allAvlSlots = driver.find_elements(
            By.CLASS_NAME, "available-slot:not(.booked-slot)"
        )
        for slot in allAvlSlots:
            div = slot.find_element(By.CLASS_NAME, "schedule-time")
            if desired_tee_time in div.text:
                try:
                    chips = slot.find_elements(By.CLASS_NAME, "player-chip-detail")
                    available_spots = 4 - len(chips)
                    if available_spots >= num_of_players:
                        ## Click BOOK in the target slot
                        slot.find_element(By.CLASS_NAME, "submit-button").click()
                        ## selects number of players from drop down
                        guestPane = driver.find_element(
                            By.CLASS_NAME, "guest-container"
                        )
                        player_options = guestPane.find_elements(By.TAG_NAME, "li")
                        player_options[num_of_players - 1].click()
                        return True
                except Exception as e:
                    print(f"Select players for afternoon tee time had an error: {e}")
                    return False
        else:
            print(f"No tee times found with {desired_tee_time}")
            return False

    except Exception as e:
        print("Waiting extra time for players to load for afternoon tee time")
        try:
            sleep(0.5)  # Wait for players window to open
            ## selects number of players
            guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
            player_options = guestPane.find_elements(By.TAG_NAME, "li")
            player_options[num_of_players - 1].click()
            return None
        except Exception as e:
            print(
                f"Select players for afternoon tee time, after waiting, had an error: {e}"
            )
            return False


## Once the time, make the tee time
def make_a_reservation() -> bool:
    """
    Make a reservation for the given time and name at the booking site.
    Return the status if the reservation is made successfully or not.
    """
    global tee_time_info
    options = Options()
    options.page_load_strategy = "normal"

    ## comment out this line to see the process in chrome
    if is_testing_mode == False:
        options.add_argument("--headless=new")  # runs the process without a browswer

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)

    def click_reservation_date(driver) -> None:
        td_days = driver.find_elements(
            By.CLASS_NAME, "mat-calendar-body-cell-container"
        )
        td_days[reservation_day - 1].click()
        return driver

    ## MAIN PAGE
    try:
        driver.get(os.environ.get("URL"))
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.ID, "mat-input-3")))

        ## fill in the username and password
        input_box = driver.find_element(By.ID, "mat-input-2")
        input_box.clear()
        input_box.send_keys(os.environ.get("USERNAME"))
        input_box = driver.find_element(By.ID, "mat-input-3")
        input_box.clear()
        input_box.send_keys(os.environ.get("PASSWORD"))
        driver.find_element(By.TAG_NAME, "button").click()
    except Exception as e:
        print(f"Unable to log in: {e}")
        return False

    ## COURSE LISTINGS PAGE
    try:
        sleep(1)  # Wait to let page load before navigating to new page
        driver.get(os.environ.get("TEESHEET_URL"))

        wait = WebDriverWait(driver, 6)  ## Wait to let page load
        wait.until(EC.presence_of_element_located((By.ID, "bookNowAccords")))
        sleep(1.5)  ## required
        allBookButtons = driver.find_elements(By.CLASS_NAME, "book__now__btn")
        allBookButtons[course_number - 1].click()
    except Exception as e:
        print("Allowing extra time for course listing page to load")
        try:
            sleep(1)  # Allow extra time for page to load
            allBookButtons = driver.find_elements(By.CLASS_NAME, "book__now__btn")
            allBookButtons[course_number - 1].click()
        except Exception as e:
            print(f"Unable to select course: {e}")
            return False

    ## TEE SHEET WITH TEE TIMES
    try:
        sleep(1.75)  ## Wait to let page load
        ## Open end tee time calendar
        date_inputs = driver.find_elements(By.TAG_NAME, "input")
        date_inputs[1].click()
    except Exception as e:
        print("Allowing extra time for Tee Sheet with tee times to load")
        try:
            sleep(
                0.5
            )  # Common spot for page to take a long time loading; allowing extra time
            date_inputs = driver.find_elements(By.TAG_NAME, "input")
            date_inputs[1].click()
        except Exception as e:
            print("Allowing double extra time for Tee Sheet with tee times to load")
            try:
                sleep(
                    3
                )  # Common spot for page to take a long time loading; allowing extra time
                date_inputs = driver.find_elements(By.TAG_NAME, "input")
                date_inputs[1].click()
            except Exception as e:
                print(f"Unable to select 1st end date: {e}")  # Errored out here 3/29
            return False
    ## change end date to this month (go back when at end of month)
    if is_previous_month == True:
        try:
            previous_month = driver.find_element(
                By.CSS_SELECTOR, "button.mat-calendar-previous-button"
            )
            previous_month.click()
        except Exception as e:
            print("Unable to select next month for end date", e)
            return False
    ## change end date to next month
    if is_current_month == False:
        try:
            next_month = driver.find_element(
                By.CSS_SELECTOR, "button.mat-calendar-next-button"
            )
            next_month.click()
        except Exception as e:
            print("Unable to select next month for end date", e)
            return False
    try:
        # select end date in date picker
        sleep(1)
        click_reservation_date(driver)
    except Exception as e:
        print("Allowing extra time for 2nd end date picker")
        try:
            sleep(1)  # Allow extra time if needed
            # select end date in date picker
            click_reservation_date(driver)
        except Exception as e:
            print(f"Unable to select 2nd end date: {e}")  # Errored out here 3/29
            return False
    try:
        # Open start tee time Calendar
        date_inputs = driver.find_elements(By.TAG_NAME, "input")
        date_inputs[0].click()
    except Exception as e:
        print("Unable to open start time calendar", e)
        return False
    # change start date to next month
    if is_current_month == False:
        try:
            next_month = driver.find_element(
                By.CSS_SELECTOR, "button.mat-calendar-next-button"
            )
            next_month.click()
        except Exception as e:
            print("Unable to select next month for end date", e)
            return False
    try:
        # select start date in date picker
        click_reservation_date(driver)
    except Exception as e:
        print("Allowing extra time for start tee time picker")
        try:
            sleep(1)  # allow extra time if needed
            # Open start tee time Calendar
            date_inputs = driver.find_elements(By.TAG_NAME, "input")
            date_inputs[0].click()
            # select start date in date picker
            click_reservation_date(driver)
        except Exception as e:
            print(f"Unable to select start date in picker: {e}")
            return False
    elapsed_time(f"At GET SLOTS: {datetime.now()}")
    # only click Get Slots when it's 19:00 Pacific
    current_time, is_during_running_time = check_current_time()
    while is_during_running_time == False:
        if not is_during_running_time:
            print(
                f"Not Running the program. It is {current_time} and not between {begin_time} and {end_time}"
            )

            # sleep less as the time gets close to the begin_time, 19:00 (7pm pacific/10pm eastern)
            if current_time >= begin_time:
                sleep(0.001)
            elif begin_time3 <= current_time < begin_time2:
                sleep(0.5)
            else:
                sleep(1)

            current_time, is_during_running_time = check_current_time()
            continue
        break
    try:
        driver.find_element(By.CLASS_NAME, "submit-button").click()
        elapsed_time(f"Clicked Book at: {datetime.now()}")
    except Exception as e:
        print(f"Unable to click get slots: {e}")
        return False

    ## CLICK BOOK & SELECT NUM OF PLAYERS IN TEE SHEET
    try:
        sleep(1)  ## Wait to let page refresh
        root_element = driver.find_element(By.TAG_NAME, "app-root")
        inner_div_element = root_element.find_element(By.TAG_NAME, "div")
        innermost_div_element = inner_div_element.find_element(By.TAG_NAME, "div")
        try:
            # Get the scroll container element
            scrollCont = innermost_div_element.find_element(By.ID, "scrollContainer")
        except Exception as e:
            print("Allowing extra time for scroll element")
            try:
                sleep(1)  ## give extra time to find scroll element
                root_element = driver.find_element(By.TAG_NAME, "app-root")
                inner_div_element = root_element.find_element(By.TAG_NAME, "div")
                innermost_div_element = inner_div_element.find_element(
                    By.TAG_NAME, "div"
                )
                scrollCont = innermost_div_element.find_element(
                    By.ID, "scrollContainer"
                )
            except Exception as e:
                if is_testing_mode == False:
                    sendEmailMessage(
                        "Unable to book tee time",
                        f"Allow extra time for scroll failed: {e}",
                    )
                else:
                    print(f"Unable to find scroll element {e}")
                return False
        # Get the height of the scroll container
        scroll_height = driver.execute_script(
            "return arguments[0].scrollHeight", scrollCont
        )

        # Check if there are no slots at all
        for element in driver.find_elements(
            By.XPATH, f"//*[contains(text(), 'No Slots Found')]"
        ):
            try:
                if element.is_displayed():
                    if is_testing_mode == False:
                        sendEmailMessage(
                            "Unable to book tee time",
                            f"No slots found on course {course_number}. Course not available",
                        )
                        # logError("No slots")
                    else:
                        print(f"No slots found on course {course_number}")
                    slots_unavailable_error = True
                    return False
                    break
            except Exception as e:
                print(f"There are no slot error {e}")
                return False
                break

        # SEARCH FOR FIRST AVAIALABLE OR BOOK BY TEE TIME/AFTERNOON ROUND
        if book_first_avail == True and afternoon_round == False:
            selectedSlot = False
            scrollTimes = 1
            # Scroll through the container until the desired tee time is found or until you've reached the bottom
            while not selectedSlot:
                for element in driver.find_elements(
                    By.XPATH, f"//*[contains(text(), 'BOOK')]"
                ):
                    try:
                        if element.is_displayed():
                            elapsed_time(f"Booking Slot Now {datetime.now()}")
                            selectedSlot = select_slot_by_first_available(driver)
                            if selectedSlot == True:
                                break
                    except Exception as e:
                        print(f"Select tee time had an error {e}")
                        return False
                        break
                else:
                    print("Scrolling -- Looking for available tee time")
                    scrollTimes += 1
                    # If the element was not found, scroll the container
                    driver.execute_script(
                        "arguments[0].scrollTop += arguments[0].offsetHeight",
                        scrollCont,
                    )
                    # Check if you've reached the bottom of the container or exceeded scroll times
                    if (
                        driver.execute_script(
                            f"return arguments[0].scrollTop", scrollCont
                        )
                        == scroll_height
                        or scrollTimes >= 20
                    ):
                        if is_testing_mode == False:
                            sendEmailMessage(
                                "Unable to book tee time",
                                f"Scrolled {scrollTimes} times. No slots found on course {course_number}. Course not available",
                            )
                            # logError("No slots")
                        else:
                            print(
                                f"Scrolled {scrollTimes} times. Unable to book a tee time. No available tee times on {course_number}"
                            )
                        tee_times_unavailable_error = True
                        return False
        else:
            selectedPlayer = False
            scrollTimes = 1
            # Scroll through the container until the desired tee time is found or until you've reached the bottom
            while not selectedPlayer:
                for element in driver.find_elements(
                    By.XPATH, f"//*[contains(text(), '{desired_tee_time}')]"
                ):
                    try:
                        if element.is_displayed():
                            # BOOK AFTERNOON ROUND
                            if afternoon_round == True:
                                select_afternoon_tee_time(driver)
                            else:
                                select_slot_by_tee_time(driver)
                            selectedPlayer = True
                            break
                    except Exception as e:
                        print(f"select tee time had an error {e}")
                        return False
                else:
                    print("Scrolling -- Looking for specific tee time")
                    scrollTimes += 1
                    sleep(0.25)  # sometimes gets hung up on scrolling
                    # If the element was not found, scroll the container
                    driver.execute_script(
                        "arguments[0].scrollTop += arguments[0].offsetHeight",
                        scrollCont,
                    )
                    # Check if you've reached the bottom of the container or exceeded scroll times
                    if (
                        driver.execute_script(
                            f"return arguments[0].scrollTop", scrollCont
                        )
                        == scroll_height
                        or scrollTimes >= 20
                    ):
                        if is_testing_mode == False:
                            sendEmailMessage(
                                "Booking A Tee Time Issue",
                                f"Scrolled {scrollTimes} times. Unable to book specified tee time. Tee times on {course_number} not availalbe for day {reservation_day}",
                            )
                        else:
                            print(
                                f"Scrolled {scrollTimes} times. Unable to book specified tee time. Tee times on {course_number} not availalbe"
                            )
                        return False
    except Exception as e:
        if is_testing_mode == False:
            sendEmailMessage(
                "Unable to book tee time",
                f"Error on {HOST_NAME}: {e}",
            )
        else:
            print(f"Unable to find and book number of players {e}")
        return False

    # GUEST INFO PAGE / SHOPPING CART
    try:
        sleep(1)  ## Wait to let page load
        wait = WebDriverWait(driver, 10)
        element = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "loader-hidden"))
        )
        if driver.current_url != 'https://pinehurstmembers.com/booking/golf/guestinfo':
            print(f"Unable to advance to shopping cart after selecting players: Means tee time is on hold: {course_number}")
            if is_testing_mode == False:
                sendEmailMessage(
                    "Tee time on hold",
                    f"Unable to advance to shopping cart after selecting players: Means tee time {course_number} is on hold",
                )
        # Choose extra players
        def book_extra_players(elementNum) -> None:
            root_element = driver.find_element(By.TAG_NAME, "app-root")
            inner_div_element = root_element.find_element(By.TAG_NAME, "div")
            innermost_div_element = inner_div_element.find_element(By.TAG_NAME, "div")
            guestInfoCont = innermost_div_element.find_element(
                By.CLASS_NAME, "guest-info-container"
            )
            elements = guestInfoCont.find_elements(By.CLASS_NAME, "mat-icon.mat-icon")
            elements[elementNum].click()
        
        # Loop through and book extra players
        if num_of_players >= 2:
            i = num_of_players
            while i > 1:
                print(i)
                i -= 1
                book_extra_players(i)
    except Exception as e:
        print("Allowing extra time for Guest Info Shopping Cart to load")
        try:
            sleep(2)  # Common spot for page to take a long time loading
            wait = WebDriverWait(driver, 10)
            element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "loader-hidden"))
            )
            # Choose extra players
            if num_of_players == 2:
                root_element = driver.find_element(By.TAG_NAME, "app-root")
                inner_div_element = root_element.find_element(By.TAG_NAME, "div")
                innermost_div_element = inner_div_element.find_element(
                    By.TAG_NAME, "div"
                )
            try:
                guestInfoCont = innermost_div_element.find_element(
                    By.CLASS_NAME, "guest-info-container"
                )
                elements = guestInfoCont.find_elements(
                    By.CLASS_NAME, "mat-icon.mat-icon"
                )
                elements[1].click()
            except Exception as e:
                print("Allowing extra time to select players")
                sleep(1)  ## allow extra time
                guestInfoCont = innermost_div_element.find_element(
                    By.CLASS_NAME, "guest-info-container"
                )
                elements = guestInfoCont.find_elements(
                    By.CLASS_NAME, "mat-icon.mat-icon"
                )
                elements[1].click()
        except Exception as e:
            if is_testing_mode == True:
                print(f"Unable to select {num_of_players} of players {e}")
            else:
                print(f"Unable to select {num_of_players} of players {e}")
                sendEmailMessage(
                    "Booking A Tee Time Issue",
                    f"Unable to select {num_of_players} players on course No. {course_number}",
                )
            return False

    try:
        sleep(0.5)  ## Wait to let page load
        tee_time_info_divs = driver.find_element(By.CLASS_NAME, "cart-header-label")
        tee_time_info = "".join(tee_time_info_divs.text)
        tee_time_info = tee_time_info.replace(" - GOLF", "")
        tee_time_info = tee_time_info.replace("\n", " - ")
        # click proceed button
        shoppingCont = driver.find_element(By.CLASS_NAME, "shopping-cart-container")
        buttons = shoppingCont.find_elements(By.TAG_NAME, "button")
        buttonIndex = int(1)  ## cancel by default
        # Find proceed button
        for i in range(len(buttons)):
            button = buttons[i]
            try:
                if button.text == "PROCEED":
                    buttonIndex = i
                break
            except Exception as e:
                print("Can't find proceed button")
                return False
        else:
            print(f"The PROCEED button was not found")
            return False

        try:
            # Check if the button at buttonIndex is clickable
            avlButtons = driver.find_elements(
                By.CSS_SELECTOR, "button[mat-raised-button]:not(.mat-button-disabled)"
            )
            enabled_buttons = len(avlButtons)
            if enabled_buttons > 1:
                buttons[buttonIndex].click()
            else:
                if is_testing_mode == True:
                    print(
                        f"Proceed button not active. Could mean an overlapping tee time"
                    )
                else:
                    print(
                        f"Proceed button not active. Could mean an overlapping tee time"
                    )
                    sendEmailMessage(
                        "Booking A Tee Time Issue",
                        f"Unable to book a tee time. May be an overlapping tee time on {course_number}",
                    )
                    return False
            # check if the overlay error box popped up
            # errorMessageFound = checkForErrorPopUp(driver)
            # if errorMessageFound == True:
            #     return False
        except Exception as e:
            print(f"Can't click proceed button. Breaking out of the loop. Error: {e}")
            return False

        # CONFIRMATION PAGE
        try:
            wait = WebDriverWait(driver, 10)  ## Wait to let page load
            element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "loader-hidden"))
            )
            # Find Confirm button
            shoppingCont = driver.find_element(
                By.CLASS_NAME, "booking-details-container"
            )
            confirm_page_buttons = shoppingCont.find_elements(By.TAG_NAME, "button")
            confirm_buttonIndex = int(1)  ## cancel by default
            for i in range(len(confirm_page_buttons)):
                button = confirm_page_buttons[i]
                try:
                    if button.text == "CONFIRM":
                        confirm_buttonIndex = i
                    break
                except NoSuchElementException:
                    pass
            else:
                print(f"The CONFIRM button was not found")
                return False

            # Test mode will not click confirm
            if is_testing_mode == True:
                elapsed_time("Testing Mode Complete")
                sleep(6)
                return True
            else:
                # Click confirm button
                confirm_page_buttons[confirm_buttonIndex].click()
                elapsed_time("Clicked confirmed")
                sleep(5)  ## Wait to let page load - required to finalize booking
        except Exception as e:
            sleep(5)  ## Wait a little longer to let the page load
            print(f"Unable to confirm {e}")
            return False
        return True
    except Exception as e:
        print(f"Issue with proceed and confirm: {e}")
        return False
    finally:
        # close the drivers
        driver.quit()


# check the time
def try_booking() -> None:
    global try_num
    global tee_times_unavailable_error  # set to true when there is an error booking a tee time
    global course_number
    global slots_unavailable_error  # Set to True when course is unavilable
    global overlay_popup_error

    """
    Try booking a reservation until either one reservation is made successfully or the attempt time reaches the max_try
    """
    # initialize the params
    current_time, is_during_running_time = check_current_time()
    reservation_completed = False
    try_num = 1
    tee_times_unavailable_error = False
    slots_unavailable_error = False
    overlay_popup_error = False

    if book_first_avail == True:
        tee_time = "first available"
    elif select_afternoon_tee_time == True:
        tee_time = "afternoon"
    else:
        tee_time = desired_tee_time

    if is_testing_mode == False:
        sendEmailMessage(
            "Booking A Tee Time",
            f"Starting at {current_time} for {tee_time} tee time on course No. {course_number} on day {reservation_day} for {num_of_players}",
        )
    else:
        print("*********** TESTING MODE ON **************")

    try:
        while True:
            print(
                f"----- try #{try_num} for {tee_time} tee time on course No. {course_number} on day {reservation_day} for {num_of_players} players -----"
            )
            print(f"The current time is {current_time}")
            # try to get tee time
            reservation_completed = make_a_reservation()
            print(f"reservation status {reservation_completed}")
            # If no errors
            if reservation_completed:
                current_time, is_during_running_time = check_current_time()
                if is_testing_mode == False:
                    sendEmailMessage(
                        "Tee Time is BOOKED!",
                        f"Booked {num_of_players} tee time(s) for {tee_time_info}.  Tried {try_num} time(s).",
                    )
                else:
                    print(
                        f"----- Tee Time Reserved for {num_of_players} players: {tee_time_info} -----"
                    )
                break
            # stop trying if no slots found for course
            elif slots_unavailable_error == True:
                current_time, is_during_running_time = check_current_time()
                print(f"No slots found for course {course_number}")
                if is_testing_mode == False:
                    sendEmailMessage(
                        "Booking Issue: Course Not Open",
                        f"No slots on {course_number} for day {reservation_day}.  Tried {try_num} time(s).",
                    )
                else:
                    print(
                        f"No slots on {course_number} for day {reservation_day}.  Tried {try_num} time(s)."
                    )
                    sleep(10)
                break
            # stop trying if overlaying pop up error was found
            elif overlay_popup_error == True:
                print(f"Overlay pop up error for course {course_number}")
                if is_testing_mode == False:
                    sendEmailMessage(
                        "Booking Issue: Overlay pop up error",
                        f"Unable to proceed on {course_number} for day {reservation_day}.  Tried {try_num} time(s).",
                    )
                else:
                    print(
                        f"Unable to proceed on {course_number} for day {reservation_day}.  Tried {try_num} time(s)."
                    )
                    sleep(10)
                break
            # stop trying if max_try is reached
            elif try_num >= max_try:
                current_time, is_during_running_time = check_current_time()
                print(f"Tried {try_num} times, but couldn't get the tee time...")
                if is_testing_mode == False:
                    if tee_times_unavailable_error == True:
                        sendEmailMessage(
                            "Booking Issue: No Tee Times Available",
                            f"No available tee times on {course_number} for day {reservation_day}.  Tried {try_num} time(s).",
                        )
                    else:
                        sendEmailMessage(
                            "Unable to Book A Tee Time",
                            f"Unable to book a tee time for {tee_time} tee time on course No. {course_number} on day {reservation_day} for {num_of_players}. Bot stopped at {current_time}.  Tried {try_num} time(s).",
                        )
                else:
                    print(
                        f"Unable to book a tee time for {tee_time} tee time on course No. {course_number} on day {reservation_day} for {num_of_players}. Bot stopped at {current_time}"
                    )
                    sleep(10)
                break
            else:
                # if random sig course, try next sig course
                if random_signature_course == True and course_number in [7, 8, 9]:
                    course_number = 7 if course_number == 9 else course_number + 1
                    tee_times_unavailable_error = False  # resets for next course
                    try_num += 1
                    print("Trying next signature course")
                else:
                    print("Bot Stopped")
                    break
    except Exception as e:
        if is_testing_mode == False:
            sendEmailMessage(
                "Error: Unable to Book A Tee Time",
                f"Unable to book a tee time on {course_number}. {e}",
            )
        print(f"Unable to book a tee time: {e}")
        return False
    finally:
        # close the SMTP server
        server.quit()


if __name__ == "__main__":
    try_booking()
