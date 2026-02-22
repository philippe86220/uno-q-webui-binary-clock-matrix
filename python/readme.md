# Linux Core Application — Code Structure Overview

This section explains the structure of the Python application running on the Linux side of the UNO Q.  

The code is organized into logical blocks, each responsible for a specific role in the system.  

---

## 1. Imports and System Initialization

This first block imports all required modules and initializes the main system components.

It includes :

- Standard Python modules for time, threading, file handling, and JSON processing.
- Timezone management using the `zoneinfo` library.
- UNO Q specific utilities such as:
  - `App` for running the application loop
  - `Bridge` for communication with the STM32
  - `Logger` for system logging
  - `WebUI` for serving the web interface and REST API.
  
This block also initializes the logger and starts the WebUI server.  

Its purpose is to prepare all external dependencies and runtime services.  

---

## 2. Shared Application State and Synchronization

This block defines the global application state stored in a dictionary called `_state`.

It contains :

- Current time and date values
- Matrix running/sleep status
- Active timezone
- Hour display mode (12h or 24h)

Because this state is accessed by multiple threads, a threading lock (`_lock`) is defined to ensure safe  
concurrent access.  

This block also defines a flag used to prevent repeated "clear matrix" commands.  

Its purpose is to centralize all dynamic system data in one shared location.

---

## 3. Configuration File Management

This block handles loading and saving persistent configuration.  

It includes :  

- The path to a local `config.json` file
- A default timezone fallback value
- A function to load configuration from disk
- A function to save updated configuration

This allows the system to remember the selected timezone and hour display mode across restarts.

---

## 4. Timezone and Display Utility Functions

This block contains helper functions used throughout the application.  

These include :

- Validating whether a timezone name is correct
- Retrieving the current active timezone safely
- Converting a 24-hour value into a 12-hour display value when required

These functions encapsulate small but important logic operations used by multiple parts of the system.

---

## 5. REST API Handlers

Each handler performs a specific task :  

- Returning the current system state (`/api/time`)
- Starting or stopping matrix updates
- Getting or setting the timezone
- Getting or setting the hour display mode

All handlers use the shared state lock to ensure thread-safe access.  

These functions do not run continuously.  
They are executed only when HTTP requests are received.  

---

## 6. Background Time Update Thread

This block contains the `_tick_loop()` function, which runs in a dedicated background thread.  

Its responsibilities include :

- Reading the current system time every second
- Updating the shared application state
- Checking whether the matrix should be active
- Sending RPC commands to the STM32 using the Bridge
- Clearing the matrix when entering sleep mode

This loop acts as a periodic scheduler that drives the entire clock update mechanism.  

---

## 7. API Registration

This block connects REST endpoints to their corresponding handler functions using  
`web.expose_api().`  

It defines :

- HTTP methods (GET or POST)
- API paths
- The function that handles each request

This effectively creates the communication interface between the WebUI and the Linux application.

---

## 8. Application Entry Point and Thread Startup

The final block contains the `main()` function.  

It performs the following steps :  

1. Loads the saved configuration
2. Initializes the shared application state
3. Starts the background time update thread
4. Launches the main application loop using `App.run()`

The `App.run()` call starts the main thread responsible for serving the WebUI and handling REST  
requests.

---

## 9. Overall Execution Model

The Linux application operates using a dual-thread model :

- The main thread runs the WebUI server and handles REST API requests.
- A background thread runs a periodic loop to update time and communicate with the STM32.

Both threads share a common state protected by a synchronization lock.



---

## Appendix A — Linux Core Code Explanation

(main.py explained line by line)

### Imports

`import datetime`
Provides access to date and time functions, used to retrieve the current system time.

`import json`
Used to read and write the configuration file stored in JSON format.

`import os`
Provides utilities for working with file paths and directories.

`import threading`
Allows the creation of a background thread for periodic time updates.

`import time`
Provides the sleep() function used to pause execution between updates.

`from zoneinfo import ZoneInfo, available_timezones`
Used for timezone management and validation.

`from arduino.app_utils import App, Bridge, Logger`
Imports UNO Q utilities :

- `App` runs the main application loop
- `Bridge` enables RPC communication with the STM32
- `Logger`provides logging capabilities

`from arduino.app_bricks.web_ui import WebUI`
Provides the WebUI server and REST API functionality.

---

### Initialization

`logger = Logger("uno-q-clock")`
Creates a logger instance for recording system events.

`print("Python ready", flush=True)`
Displays a startup message immediately.

`web = WebUI()`
Starts the WebUI server and serves the web interface automatically.

---

### Shared State and Synchronization

`_lock = threading.Lock()`
Creates a lock to protect shared data accessed by multiple threads.

`_state = {...}`
Defines a dictionary storing the global application state :   

- current time and date
- running status of the matrix
- active timezone
- hour display mode

---

### Matrix Status Flag

`_matrix_is_on = True`
Tracks whether the LED matrix is currently active, preventing repeated clear commands.

---

### Configuration File Setup

`_CONFIG_PATH = ...`
Defines the location of the persistent configuration file.

`_DEFAULT_TZ = "Europe/Paris"`
Specifies the default timezone used when configuration is missing or invalid.

---

### Configuration Management Functions

`_load_config()`
Reads configuration from disk and returns timezone and hour mode values.

`_save_config()`
Writes updated configuration values back to the JSON file.

---

### Timezone Utility Functions

`_is_valid_tz()`
Checks whether a given timezone name is valid.

`_get_tz()`
Returns the current active timezone in a thread-safe manner.

---

### Hour Display Conversion

`_hour_for_display()`
Converts a 24-hour value into a 12-hour display format if needed.

---

### REST API Handlers

`api_get_hour_mode()`
Returns the current hour display mode.

`api_set_hour_mode()`
Updates the hour display mode and saves it to the configuration file.

---

### Background Time Update Loop

`_tick_loop()`
Runs continuously in a separate thread.

Inside this loop :  

- The current system time is retrieved every second.
- The shared application state is updated.
- The matrix running status is checked.
- RPC commands are sent to the STM32:
  - `updateTime` when running
  - `clearMatrix` when entering sleep mode.
  
This loop acts as the main periodic scheduler for the application.  

---

### REST API Endpoints

`api_time()`
Returns the complete system state to the WebUI.

`api_start()`
Enables matrix updates.

`api_stop()`
Disables matrix updates.

`api_get_timezone()`
Returns the current timezone.

`api_set_timezone()`
Updates the timezone and saves it.

---

### API Registration

`web.expose_api(...)`
Associates HTTP routes with their corresponding handler functions.  

This defines the communication interface between the WebUI and the Linux application.

---

### Application Entry Point

`main()`

Initializes the system :

- Loads saved configuration
- Updates shared state values
- Starts the background thread
- Launches the main application loop

`App.run()`
Starts the main thread responsible for serving the WebUI and handling REST requests.

---

### Program Execution

`if __name__ == "__main__": main()`
Ensures that the application starts only when the script is run directly.

---


