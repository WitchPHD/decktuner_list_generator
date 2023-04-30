# decktuner_list_generator
Scrape the DeckTuner server server for information about workshops and channels, and generate several helpful lists for the mods and tuners. 

# How this tool functions:

1. Gets a list of all channels to scan.
2. Scans tuning-board for 100 messages.

	1a. Creates a workshop object with relevant information from each message.
	
	1b. If the workshop has "tuner: none" then add the workshop_id to a list.
	
3. Scans spam-log's recent 100 messages for "user left" messages.

	3a. Add the id of users that left to a list.
	
4. Scans all workshop channels.

	3a. Finds the workshop object that have the same channel_id and adds the channel name to it.
	
	3b. If the pilot's id is in the list of people that left, mark the workshop's pilot as dead with killuser().
	
	3c. If workshop matches the id of a workshop which has no tuner, set the workshop's "claimed" property to false.
	
	3d. Get the workshop's last message and compare its timestamp to the current time's timestamp. 
		
		3dα. If the message is more than 20 days old, then set as inactive with deactivate()
		
		3dβ. If the message is less than 10 days old, mark new activity with flag_new
	
5. Do some housekeeping (clear some stuff, set some variables for later math, etc).
6. Print a list of workshops whose pilot has left.
7. Print a list of workshops which are inactive (but have a tuner).
8. Print a list of tunerless workshops, constructing each entry based on the information present in the workshop.
9. Print some math.
 
