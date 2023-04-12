# Tee Time Reservation Bot


## Getting Started
Install python 3.9

```
$ python3.9 -m venv .venv
$ poetry install
```

```
$ chmod 777 run.sh
```

## To Run Application
Set all the params for creating a tee time in the top of `main.py` then run the below commands

Run it with python (not poetry)

```
$ source ./.venv/bin/activate
$ set -o allexport; source .env; set +o allexport
$ python3 main.py [<courseNum>] [<testingBool>] [<firstAvailableBool>] [<autoselectdateBool>] [<numOfPlayers>] [<randomSignatureCourseBool>] [<afternoon_round>]
```

Run it with Poetry

```
$ set -o allexport; source .env; set +o allexport
$ poetry run python3 main.py [<courseNum>] [<testingBool>] [<firstAvailableBool>] [<autoselectdateBool>] [<numOfPlayers>] [<randomSignatureCourseBool>] [<afternoon_round>]
```


### Notes
Modeled after [this](https://medium.com/@ryujimorita.1009/how-i-built-a-booking-automation-bot-to-get-a-popular-cafe-admission-ticket-851bb2f9eac0)


### Troubleshooting
Error: Selenium modual is not installed

Try to get out of virtual env (use poetry instead)
```
$ deactivate
```

If Poetry is not correct version 1.4.2
```
$ poetry -V
$ export PATH="/Users/kathyle/.local/bin:$PATH"
```
$ source ./.venv/bin/activate
$ pip3 uninstall selenium
$ pip3 install selenium
$ echo $VIRTUAL_ENV
$ source activate $VIRTUAL_ENV
```


### Notes on creating a brand new poetry python project

If you've never used poetry before run this:

```
$ poetry config virtualenvs.in-project true
```

Create a new poetry project with virtual environment .venv with Poetry
```
$ poetry new projectName
$ poetry add packageName
$ poetry install
```
