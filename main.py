import sys
from typing import Tuple
from time import sleep
from datetime import time, datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from joblib import Parallel, delayed
from selenium.webdriver.common.by import By
import os
from dotenv import load_dotenv

load_dotenv()

############################################################################################
# Be Sure to set all these params prior to running application                            #
############################################################################################
begin_time = time(5,0)
end_time = time(23,15)
# begin_time = time(22,0) # When should it start logging in and clicking "Get Slots"
# end_time = time(22,15) # When should it stop trying to get a tee time
max_try = 1 # change back to 500 when working
course_number = int(10) # course No; cradle is 10
desired_tee_time = '08:24 AM' # tee time in this format 'hh:mm AM'
reservation_day = int(11) # day of current month to book
is_current_month = True # False when reservation_day is for next month
num_of_players = 2  # Only allows 2 at the moment
############################################################################################

options = Options()
# comment out this line to see the process in chrome
# options.add_argument('--headless')

driver = webdriver.Chrome(
  service=Service(
    ChromeDriverManager()
                  .install()
  ),
   options=options
)

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
    try:
        driver.get(os.environ.get('URL'))
  ## Wait to let page load
        sleep(2)
        
	# fill in the username and password
        input_box = driver.find_element(By.ID, 'mat-input-2')
        input_box.clear()
        input_box.send_keys(os.environ.get('USERNAME'))
        input_box = driver.find_element(By.ID, 'mat-input-3')
        input_box.clear()
        input_box.send_keys(os.environ.get('PASSWORD'))
        driver.find_element(By.TAG_NAME, 'button').click()
        
  ## Wait to let page load
        sleep(.5)
        
	# Navigate to tee-sheet
        driver.get(os.environ.get('TEESHEET_URL'))

  ## Wait to let page load
        sleep(2) ## try to shave down a few .5 seconds later
        
        allBookButtons = driver.find_elements(By.CLASS_NAME, "book__now__btn")
        allBookButtons[course_number-1].click()
       
## Wait to let page load
        sleep(2) ## try to shave down a few .5 seconds later
       
        # select end tee time date
        date_inputs = driver.find_elements(By.TAG_NAME, "input")
        date_inputs[1].click()
        # selects date in date picker
        td_days = driver.find_elements(By.TAG_NAME, "td")
        td_days[reservation_day].click()
        # select start tee time date
        date_inputs = driver.find_elements(By.TAG_NAME, "input")
        date_inputs[0].click()
        # selects date in date picker
        td_days = driver.find_elements(By.TAG_NAME, "td")
        td_days[reservation_day].click()
        # get slots
        driver.find_element(By.CLASS_NAME, "submit-button").click()
        
## Wait to let page refresh
        sleep(1) ## try to shave down a few .5 seconds later
        
        slotIndex = int(1)
        ## obtain all open slots and find desired slot
        allAvlSlots = driver.find_elements(By.CLASS_NAME, "available-slot:not(.booked-slot)")
        for i, slot in enumerate(allAvlSlots):
          try:
            div = slot.find_element(By.CLASS_NAME, "schedule-time")
            if div.text == desired_tee_time:
                ## store slot index of desired slot number
                slotIndex = i
                print(f"The element with text {desired_tee_time} was found at index {i}")
            break
          except NoSuchElementException:
            pass
        else:
            print(f"The element with text {desired_tee_time} was not found")

        ## Click the button in the slot index
        allAvlSlots[slotIndex].find_element(By.CLASS_NAME, "submit-button").click()

        # selects number of players
        overlayPane = driver.find_element(By.CLASS_NAME, "guest-container")
        num_players = overlayPane.find_elements(By.TAG_NAME, "li") 
        num_players[num_of_players-1].click()
## Wait to let page load        
        sleep(1)

# Navigate to shopping cart
        guestInfoCont = driver.find_element(By.CLASS_NAME, "guest-info-container")
        elements = guestInfoCont.find_elements(By.CLASS_NAME, "mat-icon.mat-icon")
        elements[1].click()
## Wait to let page load        
        sleep(.5)
        
        # click proceed button
        shoppingCont = guestInfoCont.find_element(By.CLASS_NAME, "shopping-cart-container")
        buttons = shoppingCont.find_elements(By.TAG_NAME, "button")
        buttonIndex = int(1) ## cancel by default
        for i in range(len(buttons)):
            button = buttons[i]
            try:
              print('before', button.text)
              if button.text == 'PROCEED':
                  buttonIndex = i
                  print(f"The element with text was found at index {i}")
              break
            except NoSuchElementException:
              pass
        else:
            print(f"The element with text was not found")
## Wait to let page load        
        sleep(.5)
# Navigate to confirmation page
        buttons[buttonIndex].click()
## Wait to let page load
        sleep(60)
		
        return True
    except Exception as e:
        sleep(10)
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
    
    # TODO: Login here so that it doesn't lock out my account
    # TODO: repeat hitting 'get slots' until 
    # repreat booking a reservation every second
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

      print(f'----- try : {try_num} for {desired_tee_time} tee time on course {course_number} {current_time}-----')
      # try to get tee time
      reservation_completed = make_a_reservation()

      if reservation_completed:
          current_time, is_during_running_time = check_current_time(begin_time, end_time)
          print(f'Got a ticket!! {current_time}')
          break
      elif try_num == max_try:
          sleep(20)
          print(f'Tried {try_num} times, but couldn\'t get tickets..')
          break
      else:
          sleep(1)
          try_num += 1
          current_time, is_during_running_time = check_current_time(begin_time, end_time)


if __name__ == '__main__':
    try_booking()
