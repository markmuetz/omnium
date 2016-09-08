"""Views logs"""
import os
import logging
import datetime as dt

logger = logging.getLogger('omni')

ARGS = [(['--computer', '-c'], {'nargs': '?'}),
        (['--level', '-l'], {'default': 'DEBUG'}),
        (['--only-level', '-o'], {'nargs': '?'}),
        (['--from-time', '-f'], {'nargs': '?'}),
        (['--to-time', '-t'], {'nargs': '?'}),
        (['--search', '-s'], {'nargs': '?'})]


def parse_log(log_filename):
    import pandas as pd

    with open(log_filename, 'r') as f:
        lines = f.readlines()

    rows = []
    line = lines[0]
    lineno = 1
    logsec = line[24:36].strip()
    level = line[37:45].strip()
    msg = line[46:].strip()

    for line in lines[1:]:
        try:
            # Quick check.
            first_digit = int(line[0])
            time_str = line[:23]
            # e.g. '2016-09-03 11:08:38,501'
            # time = pd.datetools.parse_time_string(time_str)[0]
            # This is much faster:
            time = dt.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S,%f')
            continuation = False
        except ValueError:
            continuation = True
            msg += '\n' + line

        if not continuation:
            rows.append([lineno, time, logsec, level, getattr(logging, level), msg])

            logsec = line[24:36].strip()
            level = line[37:45].strip()
            msg = line[46:].strip()
        lineno += 1

    rows.append([lineno, time, logsec, level, getattr(logging, level), msg])

    return pd.DataFrame(rows, columns=['lineno', 'time', 'logsec', 'level', 'level_num', 'msg'])


def filter_df(args, df):
    import pandas as pd
    level_num = getattr(logging, args.level.upper())
    if args.only_level:
        level_num = getattr(logging, args.only_level.upper())
        df = df[df.level_num == level_num]
    else:
        df = df[df.level_num >= level_num]

    if args.from_time:
        from_time = pd.datetools.parse_time_string(args.from_time)[0]
        df = df[df.time >= from_time]

    if args.to_time:
        to_time = pd.datetools.parse_time_string(args.to_time)[0]
        df = df[df.time <= to_time]

    if args.search:
        df = df[df.msg.str.contains(args.search, case=False)]
    return df


def print_df(args, df):
    for row in df.iterrows():
        row_data = row[1]
        print('{0:4}:{1:20}:{2:8}:{3:8}:{4}'.format(row_data.lineno,
                                                    row_data.time.__str__(),
                                                    row_data.logsec,
                                                    row_data.level,
                                                    row_data.msg))


def main(args, config, process_classes):
    if not args.computer:
        log_filename = os.path.join(logger.logging_dir, 'omni.log')
    else:
        log_filename = os.path.join('logs', args.computer, 'omni.log')
    if not os.path.exists(log_filename):
        raise Exception('Log file {} does not exist'.format(log_filename))

    df = parse_log(log_filename)
    df = filter_df(args, df)
    print_df(args, df)
