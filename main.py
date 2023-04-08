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

# Set up the email parameters
EMAIL_ADDRESS = os.environ.get('EMAIL')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
sender_email = EMAIL_ADDRESS
recipient_email = EMAIL_ADDRESS

# create the email message object
msg = EmailMessage()
msg['From'] = sender_email
msg['To'] = recipient_email
msg['Subject'] = ('Booking a Tee Time')

server = smtplib.SMTP('smtp.gmail.com', 587)
server.ehlo()
server.starttls()
server.ehlo()
server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
print('Logged into SMTP successfully')

############################################################################################
# Be Sure to set all these params prior to running application                            #
############################################################################################
begin_time = time(2,0) # When should it start reserving a tee time
# begin_time = time(18,59,55) # When should it start reserving a tee time
end_time = time(19,7,0) # When should it stop trying to get a tee time
max_try = 2 # change back to 500 when working
is_current_month = True # False when reservation_day is for next month
desired_tee_time = '08:27 AM' # tee time in this format 'hh:mm AM'
course_number = int(7) # course No; cradle is 10
book_first_avail = True # True books the first available tee time on this course
num_of_players = int(2)  # Only allows 1-2 players at the moment
is_testing_mode = True # True will not book the round & will show browser window (not be headless)
reservation_day = int(8) # day of current month to book
auto_select_date_based_on_course = False # True sets the days out for booking window based on course
random_signature_course = False # True randomly chooses course No 7-9
afternoon_round = False # True picks tee time automatically in the afternoon for No 2, No 4
############################################################################################

if len(sys.argv) >= 2: # Only run the below if there are args
    course_number = int(sys.argv[1]) if len(sys.argv) >= 2 else course_number # int
    is_testing_mode = False if len(sys.argv) >= 3 and sys.argv[2] == 'False' else True # bool
    book_first_avail = False if len(sys.argv) >= 4 and sys.argv[3] == 'False' else True # bool
    auto_select_date_based_on_course = False if len(sys.argv) >= 5 and sys.argv[4] == 'False' else True # bool
    num_of_players = int(sys.argv[5]) if len(sys.argv) >= 6 else num_of_players # int
    random_signature_course = True if len(sys.argv) >= 7 and sys.argv[6] == 'True' else False # bool
    afternoon_round = True if len(sys.argv) >= 8 and sys.argv[7] == 'True' else False # bool

if random_signature_course == True and course_number in [7, 8, 9]:
    # course_number = randint(7, 9)
    max_try = 3
if afternoon_round == True:
    desired_tee_time = '02:'

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

if is_testing_mode == False:
  begin_time = time(18,59,40)
  end_time = time(19,7)

# Defaults to 10, 7, 1 days out based on course
if auto_select_date_based_on_course:
  today = date.today()
  days_out = course_booking_days_out[course_number]
  future_date = today + timedelta(days=days_out)
  reservation_day = future_date.day

  if today.month != future_date.month:
      is_current_month = False

def elapsed_time(message) -> None:
    bot_stop_time=datetime.now()
    delta = bot_stop_time - bot_start_time
    seconds = delta.total_seconds()
    print(f'{message} in {seconds} seconds')

def check_current_time() -> Tuple[time, bool]:
    '''
    Check current time is between 22:00 and 22:07.
    Returns current time and if it is between begin and end time.
    '''
    dt_now = datetime.now()
    current_time = time(dt_now.hour, dt_now.minute, dt_now.second)
    return current_time, (begin_time <= current_time) and (current_time < end_time)

# SELECT SLOT BY FIRST AVAILABLE TEE TIME
def select_slot_by_first_available(driver) -> bool:
  try:
    # obtain all open slots and find desired slot
    allAvlSlots = driver.find_elements(By.CLASS_NAME, "available-slot:not(.booked-slot)")
    for slot in enumerate(allAvlSlots):
      try:
          chips = slot.find_elements(By.CLASS_NAME, "player-chip-detail")
          available_spots = 4-len(chips)
          if available_spots >= num_of_players:
              # Click BOOK in the target slot
              slot.find_element(By.CLASS_NAME, "submit-button").click()
              sleep(1)
              # selects number of players from drop down
              guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
              player_options = guestPane.find_elements(By.TAG_NAME, "li")
              player_options[num_of_players-1].click()
              return True
      except Exception as e:
          print(f'Select players had an error: {e}')
          return False
    else:
      return False
  except Exception as e:
    print(f'Checking first available tee time error {e}')
    return False

# SELECT SLOT BY TEE TIME
def select_slot_by_tee_time(driver) -> None:
  try:
    slotIndex = int(0)
    ## obtain all open slots and find desired slot
    allAvlSlots = driver.find_elements(By.CLASS_NAME, "available-slot:not(.booked-slot)")
    for i, slot in enumerate(allAvlSlots):
      # GET BY TEE TIME
      try:
          div = slot.find_element(By.CLASS_NAME, "schedule-time")
          if div.text == desired_tee_time:
              ## store slot index of desired slot number
              slotIndex = i
              print(f"The tee time {div.text} was found at index {i}")
              break
      except Exception as e:
          print(f'First available tee time error {e}')
          return False
    else:
        print(f"The available tee time was not found")

    ## Click BOOK in the target slot
    allAvlSlots[slotIndex].find_element(By.CLASS_NAME, "submit-button").click()
    sleep(.5) # Wait for players window to open
    # selects number of players
    guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
    player_options = guestPane.find_elements(By.TAG_NAME, "li")
    player_options[num_of_players-1].click()
    return None
  except Exception as e:
    print('Waiting extra time for players to load')
    try:
      sleep(.5) # Wait for players window to open
      # selects number of players
      guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
      player_options = guestPane.find_elements(By.TAG_NAME, "li")
      player_options[num_of_players-1].click()
      return None
    except Exception as e:
      print(f'select players had an error: {e}')
      return False

# SELECT AFTERNOON TEE TIME
def select_afternoon_tee_time(driver) -> None:
  try:
    ## obtain all open slots and find desired slot
    allAvlSlots = driver.find_elements(By.CLASS_NAME, "available-slot:not(.booked-slot)")
    for slot in reversed(allAvlSlots):
        try:
            chips = slot.find_elements(By.CLASS_NAME, "player-chip-detail")
            available_spots = 4-len(chips)
            if available_spots >= num_of_players:
                # Click BOOK in the target slot
                slot.find_element(By.CLASS_NAME, "submit-button").click()
                sleep(1)
                # selects number of players from drop down
                guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
                player_options = guestPane.find_elements(By.TAG_NAME, "li")
                player_options[num_of_players-1].click()
                return True
        except Exception as e:
            print(f'Select players had an error: {e}')
            return False
    else:
        return False

    sleep(.5) # Wait for players window to open
    # selects number of players
    guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
    player_options = guestPane.find_elements(By.TAG_NAME, "li")
    player_options[num_of_players-1].click()
    return None
  except Exception as e:
    print('Waiting extra time for players to load')
    try:
      sleep(.5) # Wait for players window to open
      # selects number of players
      guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
      player_options = guestPane.find_elements(By.TAG_NAME, "li")
      player_options[num_of_players-1].click()
      return None
    except Exception as e:
      print(f'select players had an error: {e}')
      return False

# Once the time, make the tee time
def make_a_reservation() -> bool:
    '''
    Make a reservation for the given time and name at the booking site.
    Return the status if the reservation is made successfully or not.
    '''
    global tee_time_info
    starting_bot=datetime.now()
    bot_start_time=starting_bot
    options = Options()

    # comment out this line to see the process in chrome
    if is_testing_mode == False:
        options.add_argument('--headless')

    driver = webdriver.Chrome(
      service=Service(
        ChromeDriverManager()
                      .install()
      ),
      options=options
    )

    # MAIN PAGE
    try:
        driver.get(os.environ.get('URL'))
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.ID, 'mat-input-3')))
        
	      # fill in the username and password
        input_box = driver.find_element(By.ID, 'mat-input-2')
        input_box.clear()
        input_box.send_keys(os.environ.get('USERNAME'))
        input_box = driver.find_element(By.ID, 'mat-input-3')
        input_box.clear()
        input_box.send_keys(os.environ.get('PASSWORD'))
        driver.find_element(By.TAG_NAME, 'button').click()
    except Exception as e:
        print(f'Unable to log in: {e}')
        return False

    # COURSE LISTINGS PAGE
    try:
        sleep(1) # Wait to let page load before navigating to new page
        driver.get(os.environ.get('TEESHEET_URL'))

        wait = WebDriverWait(driver, 6) ## Wait to let page load
        wait.until(EC.presence_of_element_located((By.ID, "bookNowAccords")))
        sleep(1.5) ## required
        allBookButtons = driver.find_elements(By.CLASS_NAME, "book__now__btn")
        allBookButtons[course_number-1].click()
    except Exception as e:
        print('Allowing extra time for course listing page to load')
        try:
            sleep(1) # Allow extra time for page to load
            allBookButtons = driver.find_elements(By.CLASS_NAME, "book__now__btn")
            allBookButtons[course_number-1].click()
        except Exception as e:
            print(f'Unable to select course: {e}')
            return False
      
    # TEE SHEET WITH TEE TIMES
    try:
        sleep(1.75) ## Wait to let page load
        # Open end tee time calendar
        date_inputs = driver.find_elements(By.TAG_NAME, "input")
        date_inputs[1].click()
    except Exception as e:
        print('Allowing extra time for Tee Sheet with tee times to load')
        try:
            sleep(.5) # Common spot for page to take a long time loading; allowing extra time
            date_inputs = driver.find_elements(By.TAG_NAME, "input")
            date_inputs[1].click()
        except Exception as e:
            print(f'Unable to select 1st end date: {e}') # Errored out here 3/29
            return False
    # change end date to next month
    if is_current_month == False:
      try:
        next_month = driver.find_element(By.CSS_SELECTOR, "button.mat-calendar-next-button")
        next_month.click()
      except Exception as e:
        print('Unable to select next month for end date', e)
        return False
    try:
        # select end date in date picker
        td_days = driver.find_elements(By.TAG_NAME, "td")
        td_days[reservation_day].click()
    except Exception as e:
        try:
          print('Allowing extra time for 2nd end date picker')
          sleep(1) # Allow extra time if needed
          # select end date in date picker
          td_days = driver.find_elements(By.TAG_NAME, "td")
          td_days[reservation_day].click()
        except Exception as e:
          print(f'Unable to select 2nd end date: {e}') # Errored out here 3/29
          return False
    try:
        # Open start tee time Calendar
        date_inputs = driver.find_elements(By.TAG_NAME, "input")
        date_inputs[0].click()
    except Exception as e:
        print('Unable to open start time calendar', e)
        return False
    # change start date to next month
    if is_current_month == False:
      try:
        next_month = driver.find_element(By.CSS_SELECTOR, "button.mat-calendar-next-button")
        next_month.click()
      except Exception as e:
        print('Unable to select next month for end date', e)
        return False
    try:
        # select start date in date picker
        td_days = driver.find_elements(By.TAG_NAME, "td")
        td_days[reservation_day].click()
    except Exception as e:
        try:
          print('Allowing extra time for start tee time picker')
          sleep(1) # allow extra time if needed
          # Open start tee time Calendar
          date_inputs = driver.find_elements(By.TAG_NAME, "input")
          date_inputs[0].click()
          # select start date in date picker
          td_days = driver.find_elements(By.TAG_NAME, "td")
          td_days[reservation_day].click()
        except Exception as e:
          print(f'Unable to select start date in picker: {e}')
          return False
    try:
        elapsed_time('At GET SLOTS')
        # get slots
        time_to_click_slots = False
        # only click Get Slots when it's 19:00
        while time_to_click_slots == False:
          current_time, is_during_running_time = check_current_time()
          time_to_click_slots = (time(19,0,0) <= current_time) and (current_time < end_time)
          # time_to_click_slots = (time(15,21,0) <= current_time) and (current_time < time(15,40,55))
        driver.find_element(By.CLASS_NAME, "submit-button").click()
    except Exception as e:
        print(f'Unable to click get slots: {e}')
        return False

    # CLICK BOOK & SELECT NUM OF PLAYERS IN TEE SHEET
    try:
        sleep(1) ## Wait to let page refresh
        root_element = driver.find_element(By.TAG_NAME, "app-root")
        inner_div_element = root_element.find_element(By.TAG_NAME, "div")
        innermost_div_element = inner_div_element.find_element(By.TAG_NAME, "div")
        # Get the scroll container element
        scrollCont = innermost_div_element.find_element(By.ID, "scrollContainer")
        # Get the height of the scroll container
        scroll_height = driver.execute_script("return arguments[0].scrollHeight", scrollCont)

        # SEARCH FOR FIRST AVAIALABLE OR BOOK BY TEE TIME/AFTERNOON ROUND
        if book_first_avail == True and afternoon_round == False:
            selectedSlot = False
            scrollTimes = 1
            # Scroll through the container until the desired tee time is found or until you've reached the bottom
            while not selectedSlot:
                for element in driver.find_elements(By.XPATH, f"//*[contains(text(), 'BOOK')]"):
                    try:
                      if element.is_displayed():
                          selectedSlot = select_slot_by_first_available(driver)
                          if selectedSlot == True:
                            break
                    except Exception as e:
                      print(f'select tee time had an error {e}')
                      return False
                      break
                else:
                    print('Scrolling -- Looking for avilailable tee time')
                    scrollTimes += 1
                    # If the element was not found, scroll the container
                    driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight", scrollCont)
                    # Check if you've reached the bottom of the container or exceeded scroll times
                    if driver.execute_script(f"return arguments[0].scrollTop", scrollCont) == scroll_height or scrollTimes >=  20:
                        print(f'Unable to book a tee time. No available tee times on {course_number}')
                        no_tee_time_error = True
                        return False
                        break
        else:
            selectedPlayer = False
            scrollTimes = 1
            # Scroll through the container until the desired tee time is found or until you've reached the bottom
            while not selectedPlayer:
                for element in driver.find_elements(By.XPATH, f"//*[contains(text(), '{desired_tee_time}')]"):
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
                      print(f'select tee time had an error {e}')
                      return False
                      break
                else:
                    print('Scrolling -- Looking for specific tee time')
                    scrollTimes += 1
                    # If the element was not found, scroll the container
                    driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight", scrollCont)
                    # Check if you've reached the bottom of the container or exceeded scroll times
                    if driver.execute_script(f"return arguments[0].scrollTop", scrollCont) == scroll_height or scrollTimes >=  20:
                        if is_testing_mode == False:
                            del msg['subject']
                            msg['Subject'] = 'Booking A Tee Time Issue'
                            msg.set_content(f'Unable to book specified tee time. Tee times on {course_number} not availalbe for day {reservation_day}')
                            server.send_message(msg)
                        else:
                          print(f'Unable to book specified tee time. Tee times on {course_number} not availalbe')
                        return False
                        break
    except Exception as e:
        print(f'Unable to find and book number of players {e}')
        return False

    # GUEST INFO PAGE / SHOPPING CART
    try:
        sleep(1) ## Wait to let page load
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "loader-hidden")))
        # Choose extra players
        if num_of_players == 2:
            root_element = driver.find_element(By.TAG_NAME, "app-root")
            inner_div_element = root_element.find_element(By.TAG_NAME, "div")
            innermost_div_element = inner_div_element.find_element(By.TAG_NAME, "div")
            guestInfoCont = innermost_div_element.find_element(By.CLASS_NAME, "guest-info-container")
            elements = guestInfoCont.find_elements(By.CLASS_NAME, "mat-icon.mat-icon")
            elements[1].click()
    except Exception as e:
        print('Allowing extra time for Guest Info Shopping Cart to load')
        try:
            sleep(2) # Common spot for page to take a long time loading
            wait = WebDriverWait(driver, 10)
            element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "loader-hidden")))
            # Choose extra players
            if num_of_players == 2:
                root_element = driver.find_element(By.TAG_NAME, "app-root")
                inner_div_element = root_element.find_element(By.TAG_NAME, "div")
                innermost_div_element = inner_div_element.find_element(By.TAG_NAME, "div")
                guestInfoCont = innermost_div_element.find_element(By.CLASS_NAME, "guest-info-container")
                elements = guestInfoCont.find_elements(By.CLASS_NAME, "mat-icon.mat-icon")
                elements[1].click()
        except Exception as e:
          print(f'Unable to select {num_of_players} of players {e}')
          return False

    try:
        sleep(.5) ## Wait to let page load
        tee_time_info_divs = driver.find_element(By.CLASS_NAME, "cart-header-label")
        tee_time_info=''.join(tee_time_info_divs.text)
        tee_time_info = tee_time_info.replace(' - GOLF', '')
        tee_time_info = tee_time_info.replace('\n', ' - ')
        # click proceed button
        shoppingCont = driver.find_element(By.CLASS_NAME, "shopping-cart-container")
        buttons = shoppingCont.find_elements(By.TAG_NAME, "button")
        buttonIndex = int(1) ## cancel by default
        for i in range(len(buttons)):
            button = buttons[i]
            try:
              if button.text == 'PROCEED':
                  buttonIndex = i
              break
            except Exception as e:
                print("Can\'t find proceed button")
                return False
        else:
            print(f"The PROCEED button was not found")
            return False
        
        try:
            # Check if the button at buttonIndex is clickable
            avlButtons = driver.find_elements(By.CSS_SELECTOR, 'button[mat-raised-button]:not(.mat-button-disabled)')
            enabled_buttons = len(avlButtons)
            if enabled_buttons > 1:
                buttons[buttonIndex].click()
            else:
                print(f'Proceed button not active. Could mean an overlapping tee time')
                del msg['subject']
                msg['Subject'] = 'Booking A Tee Time Issue'
                msg.set_content(f'Unable to book a tee time. May be an overlapping tee time on {course_number}')
                server.send_message(msg)
                return False
        except Exception as e:
            print(f"Can\'t click proceed button. Breaking out of the loop. Error: {e}")
            return False

        # CONFIRMATION PAGE
        try: 
            wait = WebDriverWait(driver, 10) ## Wait to let page load
            element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "loader-hidden")))        
            # Find Confirm button
            shoppingCont = driver.find_element(By.CLASS_NAME, "booking-details-container")
            confirm_page_buttons = shoppingCont.find_elements(By.TAG_NAME, "button")
            confirm_buttonIndex = int(1) ## cancel by default
            for i in range(len(confirm_page_buttons)):
                button = confirm_page_buttons[i]
                try:
                  if button.text == 'CONFIRM':
                      confirm_buttonIndex = i
                  break
                except NoSuchElementException:
                  pass
            else:
                print(f"The CONFIRM button was not found")
                return False

            # Test mode will not click confirm
            if is_testing_mode == True:
                elapsed_time('Testing Mode Complete')
                sleep(6)
                return True
            else:
                # Click confirm button
                confirm_page_buttons[confirm_buttonIndex].click()
                elapsed_time('Clicked confirmed')
                sleep(5) ## Wait to let page load - required to finalize booking
        except Exception as e:
            sleep(5) ## Wait a little longer to let the page load
            print(f'Unable to confirm {e}')
            return False   
        return True
    except Exception as e:
        print(f'Issue with proceed and confirm: {e}')
        return False
    finally:
	      # close the drivers
        driver.quit()

# check the time
def try_booking() -> None:
    global try_num
    global no_tee_time_error
    global course_number
    '''
    Try booking a reservation until either one reservation is made successfully or the attempt time reaches the max_try
    '''
    # initialize the params
    current_time, is_during_running_time = check_current_time()
    reservation_completed = False
    try_num = 1
    no_tee_time_error = False
    
    if is_testing_mode == False:
      del msg['subject']
      msg['Subject'] = 'Booking A Tee Time'
      msg.set_content(f'Tee time bot checking current time starting at {current_time} on {course_number}')
      server.send_message(msg)
    else:
      print('*********** TESTING MODE ON **************')

    try:
      # repeat booking a reservation every second
      while True:
        if not is_during_running_time:
            print(f'Not Running the program. It is {current_time} and not between {begin_time} and {end_time}')

            # sleep less as the time gets close to the begin_time, 19:00 (7pm pacific/10pm eastern)
            if current_time >= time(18,59,40):
            # if current_time >= time(10,14,54):
              sleep(0.001)
            elif time(18,59,38) <= current_time < time(18,59,39):
            # elif time(10,14,52) <= current_time < time(10,14,54):
              sleep(0.5)
            else:
              sleep(1)

            current_time, is_during_running_time = check_current_time()
            continue

        if book_first_avail == True:
          tee_time = 'first available'
        elif select_afternoon_tee_time == True:
          tee_time = 'afternoon'
        else:
          tee_time = desired_tee_time
        print(f'----- try : {try_num} for {tee_time} tee time on course No. {course_number} on day {reservation_day} for {num_of_players} players -----')
        print(f'The current time is {current_time}')
        # try to get tee time
        reservation_completed = make_a_reservation()

        # If no errors
        if reservation_completed:
            current_time, is_during_running_time = check_current_time()
            if is_testing_mode == False:
              del msg['subject']
              msg['Subject'] = (f'Tee Time is BOOKED!')
              msg.set_content(f'Got {num_of_players} tee time(s) for {tee_time_info}.  Tried {try_num} time(s).')
              server.send_message(msg)
            else: 
              print(f'----- Tee Time Reserved for {num_of_players} players: {tee_time_info} -----')
            break
        # stop trying if max_try is reached
        elif try_num >= max_try:
            current_time, is_during_running_time = check_current_time()
            print(f'Tried {try_num} times, but couldn\'t get the tee time...')
            if is_testing_mode == False:
                del msg['subject']
                if no_tee_time_error == True:
                    msg['Subject'] = 'Booking Issue: No Tee Times'
                    msg.set_content(f'Unable to book a tee time. No available tee times on {course_number} for day {reservation_day}.  Tried {try_num} time(s).')
                else:
                    msg['Subject'] = 'Unable to Book A Tee Time'
                    msg.set_content(f'Unable to book a tee time on {course_number}. Bot stopped at {current_time}.  Tried {try_num} time(s).')
                server.send_message(msg)
            else:
                print(f'Unable to book a tee time. Bot stopped at {current_time}')
                sleep(10)
            break
        # if errors try again
        else:
            # if random sig course, try next sig course
            if random_signature_course == True and course_number in [7, 8, 9]:
              course_number = 7 if course_number == 9 else course_number + 1
              no_tee_time_error == False
            try_num += 1
            current_time, is_during_running_time = check_current_time()
    except Exception as e:
      if is_testing_mode == False:
        del msg['subject']
        msg['Subject'] = 'Unable to Book A Tee Time'
        msg.set_content(f'Unable to book a tee time on {course_number}. {e}')
        server.send_message(msg)
      print(f'Unable to book a tee time: {e}')
      return False
    finally:
	      # close the SMTP server
        server.quit()

if __name__ == '__main__':
    try_booking()
