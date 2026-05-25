# decktuner_list_generator
Scrape the DeckTuner server server for information about workshops and channels, and generate several helpful lists for the mods and tuners. 

To run this script successfully you must first edit two variables: 

	auth = 'my auth code is mine and you cannot have it; get your own and put it here'
	decktuner = 'put the decktuner channel ID here'
	
Replace the strings with strings containing your discord authentication code and decktuner's channel ID.

# How this tool functions:

1. Gets a list of all channels to scan.
2. Scans tuning-board for 100 messages. (note: 100 seems to be the limit of the discord API)

	1a. Creates a workshop object with relevant information from each message.
	
	1b. If the workshop has "tuner: none" then add the workshop_id to the unclaimed list.
	
3. Scans spam-log's recent 100 messages for "user left" messages.

	3a. Add the id of users that left to a list of users that left.
	
4. Scans all workshop channels.

	3a. Finds the workshop object created from the tuning-board that have the same channel_id and adds the channel name to it.
	
	3b. If the pilot's id is in the list of users that left, mark the workshop's pilot as dead with killuser().
	
	3c. If workshop matches the id of a workshop which has no tuner, set the workshop's "claimed" property to false.
	
	3d. Get the workshop's last message time and creation time, and compare timestamps to the current time. 
		
		3dα. If the last message is more than 10 days old or is from the bot, then set as inactive with deactivate()
		
		3dβ. If the workshop is less than 7 days old, mark with flag_new()
		
		3dγ. If the workshop is more than 20 old days, mark with flag_urgent()
		
		3dδ. If the workshop is more than 60 old days and unclaimed, it will be marked for deletion
	
5. Do some housekeeping (clear some stuff, set some variables for later math, etc).
6. Print a list of workshops whose pilot has left.
7. Print a list of workshops where someone used !close but it's still open.
8. Print a list of workshops which are more than 60 days old (and have no tuner).
9. Print a list of workshops which are inactive (but have a tuner).
10. Print a list of tunerless workshops (only this one is constructed for discord's format)
11. Print Tuning Bounty information
12. Print some misc info
 
