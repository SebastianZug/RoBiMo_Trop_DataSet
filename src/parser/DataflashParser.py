# This file was extracted from an existing parser for Ardupilot Log files
# https://gitlab.rrz.uni-hamburg.de/bay2789/bslogfiles/-/tree/master
# Author Marius Block 

import pandas as pd
import sys
import re

state_header = ('STATES', 'no_unit')
mode_header = ('MODES', 'no_unit')


class mode_t:
    def __init__(self, _start, _start_next, _name):
        self.start = _start
        self.start_next = _start_next
        self.name = _name

    def __str__(self):
        return '{},{},{}'.format(self.start, self.start_next, self.name)

    def __repr__(self):
        return '({})'.format(self.__str__())


def read_from_log(inputfile: str, groups: list,
                  apply_zeros=True,
                  flatline_remove=True,
                  duplicates_handler='average',
                  time_precision=1,
                  message_type = None) -> pd.DataFrame():
    # initialize all members
    date_string = ""
    m = re.search((r'.+(\d{4})[-_](\d{1,2})[-_](\d{1,2})[-_]'
                   r'(\d{1,2})[-_](\d{1,2})[-_](\d{1,2}).+'),
                  inputfile)
    if m and len(m.groups()) == 6:
        year = m.group(1)
        month = m.group(2)
        day = m.group(3)
        hour = m.group(4)
        minute = m.group(5)
        second = m.group(6)
        date_string = '{}-{}-{} {}:{}:{}'.format(
                            year, month, day, hour, minute, second)
    modes = list()
    states = list()
    messages = list()
    old_isFlying = None
    old_stage = None
    # threshold to clean noisy state changes in seconds
    # if the state toogles within threshold seconds only take the last state
    state_switch_threshold = 5
    data = pd.DataFrame()
    # statistics about logfile
    # final dict to save statistics
    log_stats = dict()
    # features which should be multiplied with zero
    zero_multiplier_feats = list()
    # features which have no change in value
    flatliner_feats = list()
    # groups with multiple measurements with same time stamp
    duplicate_groups = list()

    # the actual parsing area
    # 1.) helper data structures
    # a dict holding a list with feature names for each group
    group_features = dict()
    # a dict holding a list with measurements for each group
    group_series = dict()
    # a dict holding the units for each group
    group_units = dict()
    # a dict holding the multipliers for each group
    group_mults = dict()
    # a dict for mapping [group_string] = group_id. for parsing only.
    group_map = dict()
    # a dict for mapping unit-id to unit-string. for parsing only.
    unit_map = dict()
    # a dict for mapping multiplier-id to multiplier. for parsing only.
    mult_map = dict()
    # configuration groups or groups with text -> excluded in the following
    config_groups = ['PARM']

    # 2.) filling the group_series dictionaries for each group
    with open(inputfile, 'r') as stream:
        for line in stream:
            splits = line.split(',')
            # removing all whitespaces from splits
            splits = [s.strip() for s in splits]

            # check for UNIT group -> holding unit informations
            # UNIT line consists of
            # UNIT, TimeUS, group_id, unit_name
            if splits[0] == 'UNIT':
                assert(len(splits) == 4), 'UNIT group has false length.'
                unit_map[splits[2]] = splits[3]
            # check for MULT group -> holding multiplier informations
            # MULT line consists of
            # MULT, TimeUS, mult_id, multiplier_value
            elif splits[0] == 'MULT':
                assert(len(splits) == 4), 'MULT group has false length.'
                mult_map[splits[2]] = float(splits[3])
            # check for FMTU group -> mapping mults + units to groups
            # FMTU line consists of
            # FMTU, TimeUS, group_id, unit_id_string, mult_id_string
            elif splits[0] == 'FMTU':
                assert(len(splits) == 5), 'FMTU group has false length.'
                # convert unit_id_string to list of unit_ids
                group_units[splits[2]] = [str(ord(u)) for u in splits[3]]
                # convert mult_id_string to list of mult_ids
                group_mults[splits[2]] = [str(ord(m)) for m in splits[4]]
                #if message_type:
                #    if splits[2] == message_type:
                #        print(f"splits = {splits}")
                #        print(f"group_mults = {group_mults[splits[2]]}")
            # check for FMT group -> holding header informations
            # FMT line consists of
            # FMT, group_id, len, group_name, typeString, TimeUS, headers
            elif splits[0] == 'FMT':
                # ensure the group has a time stamp
                # assert(splits[5] == 'TimeUS'), 'FMT group has no TimeUS'
                # map group_name to group_id
                group_map[splits[3]] = splits[1]
                # retrieve features from FMT and rename it for identifying
                # after joining all DataFrames
                # use 'time' as index (aka TimeUS)
                features = ['time']
                features.extend([splits[3] + '_' + f for f in splits[6:]])
                # initialize a series with the headers of the features
                group_features[splits[3]] = features
            # Extract Mode + Timestamp
            elif splits[0] == 'MODE':
                modes.append((float(splits[1]), '#MODE {}'.format(splits[2])))
            # Extract State + Timestamp
            # splits[2] # isFlying {0,1} | splits[8] # Stage <uint>
            elif splits[0] == 'STAT':
                # if state combination changed
                if not states or old_isFlying != splits[2] \
                   or old_stage != splits[8]:
                    states.append((float(splits[1]),
                                   '#STAT isFlying{}_Stage{}'.format(
                                             splits[2], splits[8])))
                    old_isFlying = splits[2]
                    old_stage = splits[8]
            # collect messages created
            elif splits[0] == 'MSG':
                messages.append((float(splits[1]),
                                '#MSG {}'.format(splits[2])))

            # check for PARM configuration group. Ignore because no
            # measurement
            elif splits[0] in config_groups:
                continue
            # Check for a data entry
            elif groups is None or splits[0] in groups:
                # initialize a measurement list
                if splits[0] not in group_series:
                    group_series[splits[0]] = list()
                # convert a measurement to floats
                measurement = [float(m) for m in splits[1:]]
                # check if the number of features fits the NofHeaders
                assert(len(measurement) == len(group_features[splits[0]]))
                group_series[splits[0]].append(measurement)

    # 3.) constructing a DataFrame for each group
    # + invoking units and multipliers
    group_dfs = dict()
    for group_name in group_series:
        # retrieve group_id for multipliers and units
        group_id = group_map[group_name]

        # map the units
        units = [unit_map[u_id] for u_id in group_units[group_id]]
        units = [u if u else 'no_unit' for u in units]
        # assemble headers in two levels: 1. feature name, 2. unit
        headers = pd.MultiIndex.from_arrays([group_features[group_name],
                                            units],
                                            names=('time', 's'))
        # create the DataFrame
        group_dfs[group_name] = pd.DataFrame(data=group_series[group_name],
                                             columns=headers)
        # map the multipliers
        multipliers = [mult_map[m_id] for m_id in group_mults[group_id]]
        # apply the multipliers
        for mult, feat_name in zip(multipliers, group_dfs[group_name]):
            #print(feat_name, mult)
            if mult == 0:
                zero_multiplier_feats.append(feat_name[0])
                if not apply_zeros:
                    # don't apply the zero multiplier
                    continue
            group_dfs[group_name][feat_name] *= mult
        # adjust time precision
        group_dfs[group_name]['time'] = \
            group_dfs[group_name]['time'].round(time_precision)
        # set time as index
        group_dfs[group_name].set_index(('time', units[0]), inplace=True)
        # detect and deal with multiple measurements on same timestamp
        if group_dfs[group_name].index.has_duplicates:
            duplicate_groups.append(group_name)
            if duplicates_handler == 'average':
                group_dfs[group_name] =\
                    group_dfs[group_name].groupby(
                                          group_dfs[group_name].index).mean()

    # 4.) outer join all the DataFrames and sort it by time
    if not group_dfs.values():
        raise Exception('# ERROR: No requested groups found in logfile!')
    data = pd.concat(group_dfs.values(), axis=1)
    data.sort_index(inplace=True)
    # get ride of redundant index title
    data.index.name = None

    if modes:
        modes = sorted(modes, key=lambda m: m[0])
        time_multiplier_id = group_mults[group_map['MODE']][0]
        time_multipl = mult_map[time_multiplier_id]
        modes = [(round(m[0]*time_multipl, time_precision),
                  m[1]) for m in modes]
        # reduce noise switching by applying time filter
        noise = list()
        for idx in range(0, len(modes)-1):
            # if successor is less than threshold seconds away
            # mark this as noise
            if modes[idx+1][0] == modes[idx][0] or \
               (modes[idx+1][0] - modes[idx][0]) < state_switch_threshold:
                noise.append(modes[idx])
        [modes.remove(s) for s in noise]

    if states:
        states = sorted(states, key=lambda m: m[0])
        time_multiplier_id = group_mults[group_map['STAT']][0]
        time_multipl = mult_map[time_multiplier_id]
        states = [(round(m[0]*time_multipl, time_precision),
                  m[1]) for m in states]
        # reduce noise in state switching by applying time filter
        noise = list()
        for idx in range(0, len(states)-1):
            # if successor state is less than threshold x seconds away
            # mark this state as noise
            if (states[idx+1][0] - states[idx][0]) < state_switch_threshold:
                noise.append(states[idx])
        [states.remove(s) for s in noise]

    if messages:
        time_multiplier_id = group_mults[group_map['MSG']][0]
        time_multipl = mult_map[time_multiplier_id]
        messages = [(round(m[0]*time_multipl, time_precision),
                    m[1]) for m in messages]

    # joining messages, state and modes
    messages.extend(states)
    messages.extend(modes)
    messages = sorted(messages, key=lambda m: m[0])

    # retrieve and remove flatliners
    flatliner_feats = [feat[0] for feat in data
                       if feat != state_header and
                       feat != mode_header and
                       data[feat].std() == 0]
    if flatline_remove:
        data.drop(columns=flatliner_feats, level=0, inplace=True)

    # REPORTING AREA
    # report GROUP names which were requested but not found in logfile
    not_found = list()
    if groups:
        not_found = [group_name for group_name in groups
                     if group_name not in group_series]
        if not_found:
            print('# WARNING: No data found for requested groups: {}!'
                  .format(not_found), file=sys.stderr)
    log_stats['MISS'] = not_found
    log_stats['DATE'] = date_string
    log_stats['ZERO'] = zero_multiplier_feats
    log_stats['FLAT'] = flatliner_feats
    log_stats['DUPL'] = duplicate_groups

    return data, log_stats, messages


def write_csv(log: pd.DataFrame, ofname: str):
    log.to_csv(ofname)


def read_csv(ifname: str) -> pd.DataFrame:
    return pd.read_csv(ifname, header=[0, 1], index_col=0)


# choose the imputation method. returns a copy of the data but imputed.
# available 'linear' (default)
def interpolate_data(log: pd.DataFrame, how='linear') -> pd.DataFrame:
    if how == 'linear':
        return log.interpolate(method='index', limit_direction='both')
    else:
        raise Exception('# Error: Imputation Method: "{}" not available!'
                        .format(how))


# return list of dataframe slices with given flightmode
def slice_by_flightmode(log: pd.DataFrame, mode_ranges: list(),
                        cutoff=0, min_len=0) -> list():
    slices = list()
    for m in mode_ranges:
        if m.start_next == 'end':
            m.start_next = log.index.max
        if (m.start_next - (m.start + cutoff) >= min_len):
            s = log.iloc[log.index.get_loc(m.start + cutoff):
                         log.index.get_loc(m.start_next) - 1, :]
            slices.append(s)
    return slices


# mode ranges extract out of message log from parsing
def get_mode_ranges(msg: list(), kind: str, mode: str):
    if kind not in ['MODE', 'STAT']:
        raise Exception('Unknown mode type: {}'.format(kind))
    mode_ranges = list()
    start = None
    for line in msg:
        text = line[1]
        text = text.rstrip()
        m = re.search('#{} (.+)$'.format(kind), text)
        if m:
            if m.group(1) == mode:
                start = line[0]
            else:
                if start:
                    start_next = line[0]
                    mode_ranges.append(mode_t(start, start_next, mode))
                    start = None
    if start:
        mode_ranges.append(mode_t(start, 'end', mode))
    return mode_ranges
