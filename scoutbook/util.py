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

import csv

class InvalidPosition(Exception):
    pass

class DuplicateEmail(Exception):
    pass


field_mappings = {}

def init(config):
    """Initialize all of the various mappings that are needed.
    """
    populate_field_map(config)
    populate_position_map(config)
    populate_valid_scoutbook_positions(config)
    
field_map = {}
def populate_field_map(config):
    """Populate the Scoutbook to Troopmaster field map from a configuration file.
    """

    for field in config.items('Field Map'):
        field_map[field[0]] = field[1]

position_map = {}
def populate_position_map(config):
    """Populate the Troopmaster to Scoutbook position map from a configuration file.
    """

    for field in config.items('Position Map'):
        position_map[field[0]] = field[1]

valid_scoutbook_positions = []
def populate_valid_scoutbook_positions(config):
    """Populate the valid Scoutbook positions from a configuration file.
    """

    for field in config.items('Valid Scoutbook Positions'):
        valid_scoutbook_positions.append(field[0])

def populate_mapping(config, map_type):
    """Populate mapping for the given type.
    """
    mapping = {}
    for field in config.items(map_type):
        mapping[field[0]] = field[1]
    field_mappings[map_type] = mapping

def lookup_mapping(map_type, value):
    """Use the field_mappings dictionary to find a given value or return None.
    """
    try:
        return field_mappings[map_type][value]
    except:
        # If we get any exceptions on the lookup just drop through
        pass
    return None

def just_digits(str):
    input_type = type(str)
    return input_type().join(filter(input_type.isdigit, str))

def gender_mapping(str):
    """Scoutbook uses M or F for gender.  Provide a mapping.
    """

    gender_mapping = {'male': 'M',
                      'm': 'M',
                      'boy': 'M',
                      'female': 'F',
                      'f': 'F',
                      'girl': 'F',
    }

    if str.lower() in gender_mapping:
        return gender_mapping[str.lower()]
    else:
        raise ValueError('M')

def phone_fixup(str, areacode):
    value = just_digits(str)
    if not value:
        # No value allowed, just return empty string
        return ''
    elif len(value) == 7: # assume that we're missing the area code
        return '%s%s' % (areacode, value)
    elif len(value) == 10: # assume all is well
        return value
    else:
        raise ValueError('') # exception string is out default

def position_fixup(str):
    if str in position_map:
        # An assumption here is that the only position in the position map
        # are valid Scoutbook positions.
        return position_map[str]

    if not str:
        return ''
    
    # Scoutbook only allows certain positions, if the position hasn't been mapped
    # and it's not an approved position then raise an exception.
    if str in valid_scoutbook_positions:
        return str
    else:
        raise InvalidPosition


seen_emails = {}

def check_email(str):
    """Scoutbook requires that all adults have a unique email address.  This is
    what they use for their login id.  Check to see if the given email address
    has been seen before and raise an exception so that we can issue a warning.
    """

    # Future Feature:
    # Some popular email services all for + addressing so it should be possible
    # to add something like +scoutbook to the address for instance
    # bob+scoutbook@example.com.
    #
    # Also, GMail will ignore dots inside of an email address. So you could
    # easily just add a random dot to any GMail addresses, for instance
    # a.dmin@gmail.com

    # No email address, just return and we'll deal with that later.
    if not str:
        return ''
    
    if str in seen_emails:
        raise DuplicateEmail(str)

    seen_emails[str] = True

    return str
    
def create_header_array(header):
    """Take a command separated header string, parse it and return an array.
    """
    
    order = []
    for row in csv.reader([header]):
        for field in row:
            order.append(field)

    return order

scouts_by_name = {}
scouts_by_member_id = {}
def read_scout_file(filep):
    """Utility function to read in the Troopmaster scout export file so that the
    data can be used to help facilitate finding scouts from various reports.
    """

    reader = csv.DictReader(filep)

    for row in reader:
        member_id = row['BSA ID#']
        key = "%s %s" % (row['First Name'], row['Last Name'])
        scouts_by_name[key] = { 'member_id': member_id,
                                'first_name': row['First Name'],
                                'middle_name': row['Middle Name'],
                                'last_name': row['Last Name'],
        }

        # If a nickname is defined, create an additional entry with that nickname
        if row['Nickname']:
            key = "%s %s" % (row['Nickname'], row['Last Name'])
            scouts_by_name[key] = { 'member_id': member_id,
                                    'first_name': row['First Name'],
                                    'middle_name': row['Middle Name'],
                                    'last_name': row['Last Name'],
            }

        # It is possible that a scout doesn't have a member_id so we won't add them there
        if member_id:
            scouts_by_member_id[member_id] = { 'first_name': row['First Name'],
                                               'middle_name': row['Middle Name'],
                                               'last_name': row['Last Name'],
            }

def lookup_scout_by_name(name):
    """Utility function to lookup scout information by name.
    """
    try:
        return scouts_by_name[name]
    except:
        # Any exception just passthrough
        pass
    return None

def lookup_scout_by_member_id(member_id):
    """Utility function to lookup scout information by member_id.
"""
    try:
        return scouts_by_member_id[member_id]
    except:
        # Any exception just passthrough
        pass
    return None

adults_by_name = {}
adults_by_member_id = {}
def read_adult_file(filep):
    """Utility function to read in the Troopmaster adult export file so that the
    data can be used to help facilitate finding adults from various reports.
    """
    reader = csv.DictReader(filep)

    for row in reader:
        member_id = row['BSA ID#']
        key = "%s %s" % (row['First Name'], row['Last Name'])
        adults_by_name[key] = { 'member_id': member_id,
                                'first_name': row['First Name'],
                                'middle_name': row['Middle Name'],
                                'last_name': row['Last Name'],
        }

        # If a nickname is defined, create an additional entry with that nickname
        if row['Nickname']:
            key = "%s %s" % (row['Nickname'], row['Last Name'])
            adults_by_name[key] = { 'member_id': member_id,
                                    'first_name': row['First Name'],
                                    'middle_name': row['Middle Name'],
                                    'last_name': row['Last Name'],
            }

        # It is possible that an adult doesn't have a member_id so we won't add them there
        if member_id:
            adults_by_member_id[member_id] = { 'first_name': row['First Name'],
                                               'middle_name': row['Middle Name'],
                                               'last_name': row['Last Name'],
            }

def lookup_adult_by_name(name):
    """Utility function to lookup adult information by name.
    """
    try:
        return adults_by_name[name]
    except:
        # Any exception just passthrough
        pass
    return None

def lookup_adult_by_member_id(member_id):
    """Utility function to lookup adult information by member_id.
"""
    try:
        return adults_by_member_id[member_id]
    except:
        # Any exception just passthrough
        pass
    return None

