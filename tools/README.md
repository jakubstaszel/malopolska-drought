## create_database
Used to create the database for this project.
Usage:
`python -m tools.create_database`

## start_api
Starts our API that is the core for any other service to work.
Usage:

- if you want to **develop our API**:

`python -m tools.start_api -dev`

- if you want to **use it for other services**:

`python -m tools.start_api -prod`

## start_web_app
This is a Streamlit App for displaying data for małopolska drought.
Usage:

`python -m tools.start_web_app`

## process_new_imagery
Checks if new files were uploaded to Open Access Hub, if yes,
then download it and process to get WQ indexes.
Usage:

`python -m tools.process_new_imagery`

`python -m tools.process_new_imagery -f 2022-12-01 -t 2022-12-10`