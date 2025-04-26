# Networth tracking app using streamlit  

To start run requirements.txt to install the needed packages.  
- pip install -r requirements.txt  

For Windows users you have a couple options; I set up a .bat file that will start the app in the browser, and you have two options on how to run the file.  

1. Run the file from folder or a code editor
2. Follow these instructions to setup a desktop icon and run like a tradional desktop app
    - Find your .bat file in its folder location.
    - Right-click on the .bat file → choose "Create Shortcut".
    - A shortcut will appear — drag that shortcut to your Desktop.
    - Right-click on the shortcut → choose Properties.
    - In the Shortcut tab, click Change Icon...
    - Pick an icon you like from the list OR click Browse to pick your own .ico file!
    - In Properties > Shortcut, set Run to Minimized  
  
For Linux users you can run the .sh file and will start the server an run the app
- If you have problems running the file try to use 
    - dos2unix start_app.sh  
  
#### Use the take_networth_snapshot.py script to have a snapshot taken of your current networth and added to the database. The data taken from these snapshots is whats displayed in the top graph.