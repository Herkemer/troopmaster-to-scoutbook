"""
   Copyright 2015 Michael Parker

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import ConfigParser
import argparse
import csv
import re

import scoutbook.util

# This is the Scoutbook logs.csv output format
#"BSA Member ID","First Name","Middle Name","Last Name","Log Type","Date","Nights","Days","Miles","Hours","Frost Points","Location/Name","Notes"

def init_log_file(log_fp):
    """Initialize the given filename and return a csv writer object.
    """
    # Should be brand new but lets just make sure
    log_fp.truncate()

    # Go ahead and write out our header
    log_fp.write('"BSA Member ID","First Name","Middle Name","Last Name","Log Type","Date","Nights","Days","Miles","Hours","Frost Points","Location/Name","Notes"\n')

    return csv.writer(log_fp, quoting=csv.QUOTE_ALL)

# The output functions will be called via a configurable lambda so we only have one
# argument to help facilitate that configuration.  Break out the one array argument
# into individual components for output to the appropriate file.

def output_service_record(record):

    # Service entries put the credit value in the Hours field
    
    (bsa_id,
     first,
     middle_name,
     last,
     activity_date,
     credit,
     location,
     remarks) = record
    
    activity_file_mapping['Service'].writerow([bsa_id,        # BSA Member ID
                                               first,         # First Name
                                               middle_name,   # Middle Name
                                               last,          # Last Name
                                               'Service',     # Log Type
                                               activity_date, # Date
                                               '',            # Nights
                                               '',            # Days
                                               '',            # Miles
                                               credit,        # Hours
                                               '',            # Frost Points
                                               location,      # Location/Name
                                               remarks        # Note
    ])

def output_hiking_record(record):
    
    # Hiking entries put the credit value in the Miles field
    
    (bsa_id,
     first,
     middle_name,
     last,
     activity_date,
     credit,
     location,
     remarks) = record
    
    activity_file_mapping['Hiking'].writerow([bsa_id,        # BSA Member ID
                                              first,         # First Name
                                              middle_name,   # Middle Name
                                              last,          # Last Name
                                              'Hiking',      # Log Type
                                              activity_date, # Date
                                              '',            # Nights
                                              '',            # Days
                                              credit,        # Miles
                                              '',            # Hours
                                              '',            # Frost Points
                                              location,      # Location/Name
                                              remarks        # Note
    ])

def output_camping_record(record):

    # Camping entries put credit in Nights and Days as well as Frost Points
    
    (bsa_id,
     first,
     middle_name,
     last,
     activity_date,
     credit,
     location,
     remarks) = record
    
    # Troopmaster doesn't have the concept of Days so we assume Days is
    # One more than nights.
    nights = int(credit)
    days = nights + 1

    # Troopmaster does not have a concept of Frost Points so just use 0
    
    activity_file_mapping['Camping'].writerow([bsa_id,        # BSA Member ID
                                               first,         # First Name
                                               middle_name,   # Middle Name
                                               last,          # Last Name
                                               'Camping',     # Log Type
                                               activity_date, # Date
                                               str(nights),   # Nights
                                               str(days),     # Days
                                               '',            # Miles
                                               '',            # Hours
                                               '0',           # Frost Points
                                               location,      # Location/Name
                                               remarks        # Notes
    ])

# This will hold a pointer to the csv writer object for each of these activities
activity_file_mapping = {
    'Camping': None,
    'Service': None,
    'Hiking': None,
}

# Regular Expression necessary to parse the various fields from the report.
# This should cover everything unless Troopmaster adds something that isn't covered.
activity_fields = {
    'Activity Date': re.compile(r'^Activity Date:\s+(\d+/\d+/\d+)'),
    'Activity Type': re.compile('^Activity Type:\s+(.+)'),
    'Location': re.compile('^Location:\s+(.+)'),
    'Remarks': re.compile('^Remarks:\s+(.+)'),
    'Nights': re.compile('^Nights:\s+(\d+)'),
    'Hours': re.compile('^Hours:\s+([\d\.\d]+)'),
    'Miles': re.compile('^Miles:\s+(\d+)'),
    'Amount': re.compile('^Amount:\s+(\d+)'),
    'Num Scouts Attended': re.compile('(\d+) Scouts Attended'),
    'Num Adults Attended': re.compile('(\d+) Adults Attended'),
}

# Generally this text signals the start of the adult/scout listing, we want
# to know when that starts so our code doesn't get confused by other fields.
markername = re.compile(r'Marker Name')

# Regular Expression to parse out names and credit values.
people = re.compile(r'((\S+)\s+([\w-]+),\s+([\w-]+))+')

# We can parse multiple reports at one time, this regular expression helps
# us know that we are seeing a new report.
newreport = re.compile(r'^Activity Level:')

def check_match(exp, line):
    m = exp.search(line)
    if m:
        return m.group(1).strip()

# Do the hard work
def parse_activity(buf):
    found_matches = {}
    markername_p = False
    for line in buf:
        # The markername appears right before we start seeing a list of names
        # this helps keep the activity metadata fields separate and avoids
        # some accidental parsing.
        if markername.search(line):
            markername_p = True
        m = people.findall(line)
        if markername_p and m:
            # It's a name line, we may have multiples
            for item in m:
                credit = item[1]
                first = item[3]
                last = item[2]
                
                bsa_id = ''
                middle_name = ''

                # Credit value of 'X' means that we should use the overall
                # activity value.

                # Every name associated with this activities will be credited
                # with a single overall value, where that value comes from depends
                # on the type of activity

                # It appears that Troopmaster might let you change this character,
                # going to stick with the 'X' for now but note that you might need
                # to change if you've used something else.
                if credit == 'X':
                    field = scoutbook.util.lookup_mapping('Activity Credit Map',
                                                          found_matches['Activity Type'])
                    try:
                        credit = found_matches[field]
                    except KeyError:
                        # XXX - not sure this is right but in the face of no other
                        # information its the best we can do I guess
                        credit = 0

                # Attempt to find this person in the scout or adult data file
                # this isn't perfect but as long as you don't have too many
                # overlapping scouts/adults it will work well.
                # If you do have some overlapping names then output Scout Only
                # and Adult Only reports from Troopmaster and parse them separately.
                key = "%s %s" % (first, last)
                data = scoutbook.util.lookup_scout_by_name(key)
                if data:
                    bsa_id = data['member_id']
                    first = data['first_name']
                    middle_name = data['middle_name']
                    last = data['last_name']
                else:
                    data = scoutbook.util.lookup_adult_by_name(key)
                    if data:
                        bsa_id = data['member_id']
                        first = data['first_name']
                        middle_name = data['middle_name']
                        last = data['last_name']
            
                remarks = ''
                if 'Remarks' in found_matches:
                    remarks = found_matches['Remarks']

                if 'Location' not in found_matches:
                    print "There is a problem."
                    print line 
                    print found_matches
                    next

                try:
                    activity_type = found_matches['Activity Type']
                except:
                    activity_type = None

                # Output for each type is configurable so we must go lookup the output
                # function from the configuration.  If the output function exists
                # then it will be called, otherwise we log it as an unsupported
                # activity type.
                output_function = scoutbook.util.lookup_mapping('Activity Output Lambdas',
                                                                activity_type)
                if output_function:
                    # function is just a string from the config, so eval it to use it
                    output_function = eval(output_function)
                    try:
                        output_function(
                            [bsa_id, first, middle_name, last,
                            found_matches['Activity Date'],
                            credit,
                            found_matches['Location'],
                             remarks])
                    except:
                        print buf
                        raise
                else:
                    print "Unsupported Activity Type: %s" % (found_matches['Activity Type'],)
        else:
            for act in activity_fields:
                val = check_match(activity_fields[act], line)
                if val:
                    found_matches[act] = val
                    #print "%s: %s" % (act, val)


def main():

    parser = argparse.ArgumentParser(description="Process Troopmaster Scout File")

    parser.add_argument('infile', type=argparse.FileType('rb'))
    parser.add_argument('--config', required=True, type=argparse.FileType('rb'),
                        metavar='activity.cfg', default='activity.cfg')
    parser.add_argument('--adult-infile', required=False, type=argparse.FileType('rb'),
                        metavar='Adult.txt', default='Adult.txt',
                        help='Troopmaster Adult export file.')
    parser.add_argument('--scout-infile', required=False, type=argparse.FileType('rb'),
                        metavar='Scout.txt', default='Scout.txt',
                        help='Troopmaster Scout export file.')
    parser.add_argument('--hiking-logs', required=False, type=argparse.FileType('wb'),
                        metavar='hikinglogs.csv', default='hikinglogs.csv',
                        help='CSV file containing Hiking information,')
    parser.add_argument('--service-logs', required=False, type=argparse.FileType('wb'),
                        metavar='servicelogs.csv', default='servicelogs.csv',
                        help='CSV file containing Service information,')
    parser.add_argument('--camping-logs', required=False, type=argparse.FileType('wb'),
                        metavar='campinglogs.csv', default='campinglogs.csv',
                        help='CSV file containing Camping information,')
    args = parser.parse_args()

    config = ConfigParser.ConfigParser(allow_no_value=True)
    config.optionxform = str # Makes items case sensitive
    config.readfp(args.config)

    scoutbook.util.populate_mapping(config, 'Activity Credit Map')
    scoutbook.util.populate_mapping(config, 'Activity Output Lambdas')

    # Troopmaster seems to output names in it's activity report using just the
    # first and last name of the scout/adult, and usually with the nickname.
    # Since we want to output first/middle/last in addition to any BSA ID we have
    # then we want to parse the Scout and Adult output files to help fill in that
    # information.
    
    # Luckily it appears that Troopmaster only outputs "active" scouts/adults in
    # the activity reports, so as long as the activity reports and scout/adult
    # output files are generated at the same time we shouldn't get any unknown
    # entries.
    
    scoutbook.util.read_scout_file(args.scout_infile)
    scoutbook.util.read_adult_file(args.adult_infile)

    activity_file_mapping['Camping'] = init_log_file(args.camping_logs)
    activity_file_mapping['Service'] = init_log_file(args.service_logs)
    activity_file_mapping['Hiking'] = init_log_file(args.hiking_logs)

    buf = []

    for line in args.infile:
        if newreport.findall(line):
            parse_activity(buf)
            buf = []
        else:
            buf.append(line)
    # We will be left with one file buffer to parse, so go parse that
    parse_activity(buf)
    
if __name__ == '__main__':
    main()
