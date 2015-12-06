# troopmaster-to-scoutbook

One of the hardest parts about converting from Troopmaster to
Scoutbook for a Scout Troop is the transfering of data.  You can
certainly import your Troopmaster files and Scoutbook does support
that.  It seems that you have far greater control over your data (and
I think it's also faster) if you import the data in the csv format
expected by Scoutbook.

Scoutbook provides a primer for doing this import, including sample
files here:
https://www.scoutbook.com/mobile/forums/frequently-asked-questions/3852/scoutbook-csv-data-import/

The scripts in this repository represent many hours of trial and error
on getting data out of Troopmaster and massaging it into the right
format for Scoutbook.  Due to the way that Troopmaster can be
"customized" some of the choices made by the scripts may not work
properly for your unit.  You should treat this as a starting point and
adjust as necessary.  I wish I could provide a turnkey solution but
there are just too many different combinations to make that feesible.

# Exporting of Data From Troopmaster

Here are the steps necessary to export your data from Troopmaster:

File -> Export -> ASCII Delimited...

Scout.txt file:
    Check Include field names as first line of export
    Format: Comma delimited
    Select area: Scout Data
    Date Format: MM/DD/YYYY
    Members: All Scouts
    Click "Add All>>"

    Export

Adult.txt file:
    Check Include field names as first line of export
    Format: Comma delimited
    Select area: Adult Data
    Date Format: MM/DD/YYYY
    Members: All Adults
    Click "Add All>>"

    Export

Reports:
    Reports -> Activities -> Individual Activities...

    Display Level: All Levels
    Display Types: All Activity Types

    Select All Activities

    Check: Include scout attendance
    Un-Check: Include adult attendance

    Select

    Save as Text report

# Data Not Exported

You should utilize ScoutNET for all completed advancement and training
records.  If you aren't using Internet Advancement, now is an
excellent time to start.

# Scripts

scout.py
    Parse the exported scout data file into something appropriate for Scoutbook.

adult.py
    Parse the exported adult data file into something appropriate for Scoutbook.

parse_activity_report.py
    Parse the activity report into something appropriate for Scoutbook.

