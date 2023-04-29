# decktuner_list_generator
Scrape the DeckTuner server server for information about workshops and channels, and generate several helpful lists for the mods and tuners. 

# How this tool functions:

1. Scans workshop-board for 100 messages

	1a. Creates a workshop object with relevant information from each message
	
	1b. If the workshop has "tuner: none" then add the workshop_id to a list
	
2. Scans spam-log's recent 100 messages for "user left" messages and records the user_id of the user that left
3. Scans all workshop channels and...

	3a. Finds the workshop object that have the same channel_id and adds the channel name to it
	
	3b. If the pilot's id is in the list of people that left, mark the workshop as pilotless with killuser()
	
	3c. If workshop matches the id of a workshop which has no tuner, set the workshop's "claimed" property to false.
	
	3d. Get the workshop's last message and compare its timestamp to the current time's timestamp. If the message is more than 20 days old, then set the workshop's "active" propety to false.
	
4. Do some housekeeping (clear some stuff, set some variables for later math, etc).
5. Print a list of workshops whose pilot has left.
6. Print a list of workshops which are inactive (but have a tuner)
7. Print a list of tunerless workshops.
8. Print some math.
 
