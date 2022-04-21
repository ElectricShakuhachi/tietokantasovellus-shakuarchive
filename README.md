# ShakuArchive

ShakuArchive is a web archive, search tool and viewer for sheet music.

On the main page, the page will display a list of publicly available compositions and options to filter them based on musical style, composer, difficulty and other categories.
The user may also search for music by input to a search bar. Compositions will primarily be returned by matching or similar words in composition name, secondarily on matches in other data relating to the compositions.

Each list item is a link which will open another page where the sheet music can be viewed and downloaded. The page will also list information on the given musical piece and a recording, or a link to one - if such is available.

On the main page, the user may log in, after which they are able to upload sheet music on the site, either publicly, or visible to themselves only. The user may also select other user accounts specifically that are to have access to the composition. On the main page, there will also be filters to show only compositions uploaded by oneself, or by specific other users, or compositions uploaded by someone and specifically shared to the logged in user.

The files uploaded to the site must be in pdf format, and audio files may be provided in wav format. 

Developed in case there is time:

The page has two types of users, regular and admin. Users with admin rights may edit or delete compositions posted by other users. Users can also add edit rights to compositions they have themselves posted or to which they have edit rights to.

# Current Situation of Develoment:

## For Intermediate Inspection 2:

Currently the application provides the basic functionalities of being able to sign up, log in and out, view uploaded sheet music and metadata on them, and to upload if logged in.

The address of the app in Heroku is:
https://shakuarchive.herokuapp.com/

Signing up, logging in and out are self explanatory.
After creating and account and logging in, any pdf files (note: only pdf files accepted) can be uploaded from the form that opens by pressing "Upload Music"
There are no specific checks toward what is filled in as information about the music, besides that Instrument count should be filled in with an integer value, even though it is currently implemented as a textbox.

Uploaded files can be seen from links on front page.
Currently anyone may delete uploaded files - this functionality will be restricted to admin users later.

Currently pdf files are loaded to the site as static files, but they are planned to be stored in database as binary data later.

Make note of if you will of the unfamiliar look of the example piece of sheet music uploaded... 
It's traditional Japanese notation for shakuhachi flutes.

# NOTES - remove!

Now getting internal server error when pressing remove -> but it does remove

TODO:

- make results listable by any category
- make it possible for users to note what they are working on - so that people may know who to contact for hints and so on
- has to have between 5-10 tables
- monta -moneen taulu ainakin yksi
- yksi moneen kannattaa viitata viiteavaimella

