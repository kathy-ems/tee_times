# Tee Time Reservation Bot


## Getting Started
Install python 3.9

Create virtual environment .venv


```
$ python3.9 -m venv .venv
$ poetry config virtualenvs.in-project true
$ poetry install
```

```
$ chmod 777 run.sh
```

## To Run Application
Set all the params for creating a tee time in the top of `main.py` then run the below commands


```
$ source ./.venv/bin/activate
$ set -o allexport; source .env; set +o allexport
$ python3 main.py [<courseNum>] [<testingBool>] [<firstAvailableBool>] [<autoselectdateBool>] [<numOfPlayers>]
```


### Notes
Modeled after [this](https://medium.com/@ryujimorita.1009/how-i-built-a-booking-automation-bot-to-get-a-popular-cafe-admission-ticket-851bb2f9eac0)


### Troubleshooting
Error: Selenium modual is not installed

```
$ source ./.venv/bin/activate
$ pip3 uninstall selenium
$ pip3 install selenium
$ echo $VIRTUAL_ENV
$ source activate $VIRTUAL_ENV
```
