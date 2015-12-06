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
import sys

import scoutbook.util

field_fixups = {
    'Unit Number': lambda str: args.unit_number,
    'Unit Type': lambda str: 'troop',
    'LDS': lambda str: 'Y' if (args.is_lds) else 'N',
    'Home Phone': lambda str: scoutbook.util.phone_fixup(str, args.area_code),
    'Gender': scoutbook.util.gender_mapping,
}

# Scoutbook requires you to fill these values out at a minimum
required_fields = [
    'First Name',
    'Last Name',
    'Zip',
    'DOB',
    'Patrol Name',
    'Date Joined Patrol',
    'Unit Number',
    'Unit Type',
    ]

# All of the available fields for the Scoutbook input file
header_string = 'First Name,Middle Name,Last Name,Suffix,Nickname,Address 1,Address 2,City,State,Zip,Home Phone,BSA Member ID,Gender,DOB,School Grade,School Name,LDS,Swimming Classification,Swimming Classification Date,Unit Number,Unit Type,Patrol Name,Date Joined Patrol,Parent 1 Email,Parent 2 Email,Parent 3 Email'

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Process Troopmaster Scout File")

    parser.add_argument('infile', type=argparse.FileType('rb'), metavar='Scout.txt')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('wb', 0),
                        metavar='scouts.csv', default=sys.stdout)
    parser.add_argument('--config', required=False, type=argparse.FileType('rb'),
                        metavar='scoutbook.cfg', default='scoutbook.cfg')
    parser.add_argument('--unit-number', type=str, metavar='Num', required=True,
                        help='Troop unit number you will be using in Scoutbook.')
    parser.add_argument('--area-code', type=str, metavar='Num', required=True,
                        help='Primary area code for member phone numbers.')
    parser.add_argument('--is-lds', action='store_true', default=False,
                        help='Set if this is an LDS troop.')
    args = parser.parse_args()

    config = ConfigParser.ConfigParser(allow_no_value=True)
    config.optionxform = str # Makes items case sensitive
    config.readfp(args.config)

    scoutbook.util.populate_field_map(config)
    
    header_order = scoutbook.util.create_header_array(header_string)

    output = []
    output.append(header_order)

    reader = csv.DictReader(args.infile)

    for row in reader:
        # Just getting these values for debug purposes
        first = row[scoutbook.util.field_map['First Name']]
        last = row[scoutbook.util.field_map['Last Name']]
        bsaid = row[scoutbook.util.field_map['BSA Member ID']]

        newrow = []
        for header in header_order:
            try:
                value = row[scoutbook.util.field_map[header]]
            except KeyError, e: # Not found, use empty value
                value = ''

            if header in field_fixups:
                try:
                    value = field_fixups[header](value)
                except ValueError, e:
                    print "Warning %s (%s) is not valid for %s %s (%s). Defaulting to %s." % (header, value, first, last, bsaid, e)
                    value = e

            if header in required_fields and not value:
                print "Warning missing %s field for %s %s (%s)" % (header,
                                                                   first,
                                                                   last,
                                                                   bsaid)

            newrow.append(value)

        output.append(newrow)

    csv.writer(args.outfile).writerows(output)


