import sys
from typing import Tuple
from time import sleep
from datetime import time, datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from joblib import Parallel, delayed
from selenium.webdriver.common.by import By
import os
from dotenv import load_dotenv

load_dotenv()

############################################################################################
# Be Sure to set all these params prior to running application                            #
############################################################################################
begin_time = time(9,57) # When should it start reserving a tee time
end_time = time(22,7) # When should it stop trying to get a tee time
max_try = 2 # change back to 500 when working
course_number = int(7) # course No; cradle is 10
desired_tee_time = '07:06 AM' # tee time in this format 'hh:mm AM'
reservation_day = int(10) # day of current month to book
is_current_month = True # False when reservation_day is for next month
num_of_players = 2  # Only allows 1-2 players at the moment
book_first_avail = True # Book the first available tee time on this course
testing_mode = True # True will not book the round
############################################################################################

est = timezone(timedelta(hours=-8), 'EST')

def check_current_time(begin_time:time, end_time:time) -> Tuple[time, bool]:
    '''
    Check current time is between 22:00 and 22:15. 
    Returns current time and if it is between begin and end time.
    '''
    dt_now = datetime.now(est)
    current_time = time(dt_now.hour, dt_now.minute, dt_now.second)
    return current_time, (begin_time <= current_time) and (current_time < end_time)
  
# Once the time is 10pm, make the tee time
def make_a_reservation() -> bool:
    '''
    Make a reservation for the given time and name at the booking site.
    Return the status if the reservation is made successfully or not.
    '''
    options = Options()
    # comment out this line to see the process in chrome
    if testing_mode == False:
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
        print(f'Unable to select course: {e}')
        return False
      
    # TEE SHEET WITH TEE TIMES
    try:
        sleep(1) ## Wait to let page load
    
        # Open end tee time calendar
        date_inputs = driver.find_elements(By.TAG_NAME, "input")
        date_inputs[1].click()
    except Exception as e:
        print(f'Unable to select 1st end date: {e}')
        return False
      
    try:
        # select end date in date picker
        td_days = driver.find_elements(By.TAG_NAME, "td")
        td_days[reservation_day].click()
    except Exception as e:
        print(f'Unable to select 2nd end date: {e}')
        return False
      
    try:
        # Open start tee time Calendar
        date_inputs = driver.find_elements(By.TAG_NAME, "input")
        date_inputs[0].click()
        # select start date in date picker
        td_days = driver.find_elements(By.TAG_NAME, "td")
        td_days[reservation_day].click()
        # get slots
        driver.find_element(By.CLASS_NAME, "submit-button").click()
    except Exception as e:
        print(f'Unable to select start date: {e}')
        return False

    # SELECT PLAYERS IN TEE SHEET & CLICK BOOK
    try:
        sleep(1) ## Wait to let page refresh
        root_element = driver.find_element(By.TAG_NAME, "app-root")
        inner_div_element = root_element.find_element(By.TAG_NAME, "div")
        innermost_div_element = inner_div_element.find_element(By.TAG_NAME, "div")
        # # Get the scroll container element
        scrollCont = innermost_div_element.find_element(By.ID, "scrollContainer")

        # # Get the height of the scroll container
        scroll_height = driver.execute_script("return arguments[0].scrollHeight", scrollCont)
        
        def select_num_players(driver, desired_tee_time, num_of_players) -> None:
          try:
            slotIndex = int(1)
            ## obtain all open slots and find desired slot
            allAvlSlots = driver.find_elements(By.CLASS_NAME, "available-slot:not(.booked-slot)")
            for i, slot in enumerate(allAvlSlots):
              try:
                div = slot.find_element(By.CLASS_NAME, "schedule-time")
                if div.text == desired_tee_time:
                    ## store slot index of desired slot number
                    slotIndex = i
                    print(f"The element with text {div.text} was found at index {i}")
                    break
              except NoSuchElementException:
                pass
            else:
                print(f"The element with text {desired_tee_time} was not found")

            ## Click BOOK in the target slot
            allAvlSlots[slotIndex].find_element(By.CLASS_NAME, "submit-button").click()
            sleep(1)
            # selects number of players
            guestPane = driver.find_element(By.CLASS_NAME, "guest-container")
            num_players = guestPane.find_elements(By.TAG_NAME, "li")
            num_players[num_of_players-1].click()
            return False
          except Exception as e:
            print(f'select players had an error {e}')
            return False

        selectedPlayer = False
        # Scroll through the container until the desired text is found or until you've reached the bottom
        while not selectedPlayer:
            for element in driver.find_elements(By.XPATH, f"//*[contains(text(), '{desired_tee_time}')]"):
                try:
                  if element.is_displayed():
                      print(f"Found the desired text: {element.text}")
                      select_num_players(driver, desired_tee_time, num_of_players)
                      selectedPlayer = True
                      break
                except Exception as e:
                  print(f'select tee time had an error {e}')
                  break
            else:
                # If the element was not found, scroll the container
                driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight", scrollCont)
                # Check if you've reached the bottom of the container
                if driver.execute_script(f"return arguments[0].scrollTop", scrollCont) == scroll_height:
                    break
    except Exception as e:
        print(f'Unable to number of players {e}')
        return False

    # GUEST INFO PAGE / SHOPPING CART
    try:
        sleep(1.5) ## Wait to let page load
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
        print(f'Unable to {num_of_players} of players {e}')
        return False

    try:
        sleep(.5) ## Wait to let page load  
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
            except NoSuchElementException:
              pass
        else:
            print(f"The PROCEED button was not found")
        buttons[buttonIndex].click()

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

            # Test mode will not click confirm
            if testing_mode == True:
                sleep(5)
                print('Testing Mode Complete')
                return False
            else:
                # Click confirm button
                confirm_page_buttons[confirm_buttonIndex].click()
                sleep(4) ## Wait to let page load - required to finalize booking
        except Exception as e:
            print(f'Unable to confirm {e}')
            return False   
        return True
    except Exception as e:
        print(e)
        return False
    finally:
	# close the drivers
        driver.quit()

# login and check the time and click 'get slots' to keep page active
def try_booking() -> None:
    '''
    Try booking a reservation until either one reservation is made successfully or the attempt time reaches the max_try
    '''
    
    # initialize the params
    current_time, is_during_running_time = check_current_time(begin_time, end_time)
    reservation_completed = False
    try_num = 1
    bot_start_time=datetime.now()
    bot_stop_time=datetime.now()
    
    # repeat booking a reservation every second
    while True:
      if not is_during_running_time:
          print(f'Not Running the program. It is {current_time} and not between {begin_time} and {end_time}')

          # sleep less as the time gets close to the begin_time
          if current_time >= time(23,59,59):
            sleep(0.001)
          elif time(23,59,58) <= current_time < time(23,59,59):
            sleep(0.5)
          else:
            sleep(1)

          try_num += 1
          current_time, is_during_running_time = check_current_time(begin_time, end_time)
          continue

      print(f'----- try : {try_num} for {desired_tee_time} tee time on course No. {course_number} -----')
      print(f'The current time is {current_time}')
      bot_start_time=datetime.now()
      # try to get tee time
      reservation_completed = make_a_reservation()

      # If no errors
      if reservation_completed:
          current_time, is_during_running_time = check_current_time(begin_time, end_time)
          bot_stop_time=datetime.now()
          delta = bot_stop_time - bot_start_time
          seconds = delta.total_seconds()
          print(f'Got a tee time in {seconds} seconds')
          break
      # stop trying if max_try is reached
      elif try_num >= max_try:
          sleep(20)
          print(f'Tried {try_num} times, but couldn\'t get the tee time...')
          break
      # if errors try again
      else:
          sleep(1)
          try_num += 1
          current_time, is_during_running_time = check_current_time(begin_time, end_time)


if __name__ == '__main__':
    try_booking()
