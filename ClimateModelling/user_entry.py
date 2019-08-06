import argparse
from calendar import monthrange
from extract import *
from analysis import *
from write_output import *
from plots import *
import directories


# Booleans set when user gives a just a year (or a year and month)
class StartBools:
    just_start_year = False
    just_start_year_month = False


def check_valid_order(start_date, end_date):
    """
    Checks that end date is after start date
    :param start_date: [day, month, year]
    :param end_date: [day, month, year]
    :return: true if end_date is after start date
    """

    day_s, mon_s, yr_s = start_date[0], start_date[1], start_date[2]
    day_e, mon_e, yr_e = end_date[0], end_date[1], end_date[2]

    start = date(yr_s, mon_s, day_s)
    end = date(yr_e, mon_e, day_e)

    return (end - start).days > 0


def get_date(date_entry, start=True):
    """
    Separate date  d-m-y into day, month and year
    :param date_entry: string containing date e.g. 2020-04
    :param start: if set, then it is the start date of the analysis, else it is the end date
    :return: day, month, year (all integers)
    """

    try:
        date_ = map(int, date_entry.split('-'))
        date_list = list(date_)
    except ValueError:
        print("Error in function get_date(): Date written in unrecognisable format. Please try again.")
        return None

    len_d = len(date_list)
    day = 1
    month = Month.January
    year = date_list[0]
    if len_d == 1:  # Only the year is given
        StartBools.just_start_year = True
        if not start:
            day = 31
            month = Month.December
    elif len_d == 2:  # year and month are given
        StartBools.just_start_year_month = True
        month = date_list[1]
        if not start:
            day = monthrange(year, month)[1]
    elif len_d == 3:  # day, year and month are given
        day = date_list[2]
        month = date_list[1]
    else:
        print("Error in function get_date(): too many split arguments")

    # check that these are valid dates
    try:
        datetime(year, month, day)
    except ValueError:
        print("Error in function get_date(): invalid date")
        return None

    return day, month, year


def file_entry(example=False):
    filename = directories.INPUT_FILE
    if example:
        filename = directories.INPUT_EXAMPLE_FILE

    # Save arguments
    args = []
    # open a file using with statement
    with open(filename, 'r') as fh:
        for curline in fh:
            # check if the current line
            # starts with "#"
            if "#" not in curline and len(curline) > 1:
                arg = curline.split(':')[1].strip()
                args.append(arg)

    # Check if any required arguments are not filled in
    for i in range(4):
        if len(args[i]) == 0:
            print("Error: the input file has missing required arguments.")
            sys.exit()

    # Check if any optional arguments are not filled in
    for i in range(4, 16):
        if len(args[i]) == 0:
            args[i] = False
        elif args[i].lower() == 'false' or args[i].lower() == 'f':
            args[i] = False
        elif args[i].lower() == 'true' or args[i].lower() == 't':
            args[i] = True

    # histogram option
    if len(args[12]) == 0 or not args[12]:
        hist = 'fd'

    algae_type, start, ens, end = args[0], args[1], int(args[3]), args[4]
    plot, monthly, grid, sample, mask, output, covary, hist = args[5], args[6], args[7], args[8], args[9], args[10], args[11], args[12]
    lb = args[13]
    save_ext = args[14]
    func = args[15]

    # Check for plot
    if plot:
        plot = [int(plot.strip())]
    # Check for grid and sample
    if args[7]:
        grid = args[7].split(',')
        try:
            grid[0] = float(grid[0].strip())
            grid[1] = float(grid[1].strip())
        except Exception:
            print("Error in function file_entry: Argument may be missing a comma.")
            sys.exit()
    elif args[8]:
        sample = args[8].split(',')
        try:
            sample[0] = float(sample[0].strip())
            sample[1] = float(sample[1].strip())
        except Exception:
            print("Error in function file_entry: Argument may be missing a comma.")
            sys.exit()

    # Check for longitude centre
    if args[13]:
        try:
            lb = [float(lb.strip())]
        except Exception:
            print("Error in function file_entry: Longitude centre may not be a float.")
            sys.exit()

    # Get variables and put in list
    varbs = args[2].split(',')
    for i in range(len(varbs)):
        varbs[i] = varbs[i].strip()

    # Check for user function
    if func:
        func = func.split(',')
        try:
            func[0] = func[0].strip()
            func[1] = func[1].strip()
        except Exception:
            print("Error in function file_entry: Argument may be missing a comma.")
            sys.exit()

    return algae_type, start, varbs, ens, end, plot, monthly, grid, sample, mask, output, covary, hist, lb, save_ext, func


def user_entry():
    """
    Get user input
        - algae type
        - start_date
        - end_date
        - variables
        - plot option
    """
    parser = argparse.ArgumentParser(prog='CLIMATE_ANALYSIS',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     description="""The functions will give statistical analysis of the climate data 
                                     presented
    FILENAMES FORMAT
    ----------------
    - The filenames should be in the format "{START OF FILENAME}_ens{NUM}_{YEAR}.nc", where {START OF FILENAME} is 
    the prefix of the file, this can be the algae type etc, {NUM} is the ensemble number and {YEAR} is the year. 
   OR if you have multiple years stored in one file then:
   - The filenames should be in the format "{START OF FILENAME}_ens{NUM}_{YEAR 1}_{YEAR 2}.nc", where 
   {START OF FILENAME} is the prefix of the file, this can be the algae type etc, {NUM} is the ensemble number and 
   {YEAR 1} and {YEAR 2} are the start and end year of the data in the file. 
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ASSUMPTIONS
    ------------
    - Files do not have overlapped data.
    - Daily increments of data, except if the monthly tag is set in the arguments.
    - Grids have constant latitude and longitude.
    ------------
    - Some example files are in the data folder.
    """)
    parser._optionals.title = "other arguments"
    parser.add_argument('prefix', help="This is the prefix of the file. This can be the type of algae "
                                       "e.g. dic_deltap, fndet_100, jprod_ndi_100. ")
    parser.add_argument('start_date', help="""Start date of analysis 
    Can be in the following formats:
    ----------------------------------
    YYYY-MM-DD : e.g. 2020-04-12
    YYYY-MM    : e.g. 2020-04
    YYYY       : e.g. 2020 
    - If day is not given, the 1st of the given month will be used i.e 2020-04 => 2020-04-01
    - If day and month is not given, 1st Jan will be used as the start date i.e 2020 => 2020-01-01""")
    parser.add_argument('end_date', nargs='?', help=""" <Not required> End date of analysis - format is the same as start_date
    -----------------------------------end_date not given-------------------------------------
    - If only start year is given, the end_date is automatically set to the 31 Dec of start year
    - If start year and month is given, then end_date is set to the end of the start month
       -----------------------------------end_date given-------------------------------------
    - If day is not given, the end of the given month will be used i.e 2020-04 => 2020-04-30
    - If day and month is not given, 31 Dec will be used as the end date i.e 2020 => 2020-12-31""")
    parser.add_argument('-v', '--vars', nargs='+', metavar="variables", help="<Required> Variables of data to analyse",
                        required=True)
    parser.add_argument('-p', '--plot', nargs=1, metavar=("ensemble_number"), help="""Plot map, histogram and timeseries graphs
    E.g. --plot 1
    The ensemble to plot must be included. """)
    parser.add_argument('-m', '--monthly', action="store_true", help="Data in file is stored in monthly increments.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-g', '--grid', nargs=2, type=float, metavar=("lat", "lon"), help="Uses grid point that "
                                                                                         "latitude and longitude lies "
                                                                                         "in.")
    group.add_argument('-s', '--sample', nargs=2, type=float, metavar=("lat", "lon"), help="Uses sample point given by"
                                                                                           " latitude and longitude "
                                                                                           "using interpolation.")
    group.add_argument('-lc', '--lon_centre', nargs=1, type=float, help="Longitude to centre map on.")
    parser.add_argument('-mk', '--mask', nargs=1, metavar="filename", help="Uses masking grid given as a file "
                                                                           "(contains boolean array to be imposed on "
                                                                           "the global grid).")
    parser.add_argument('-o', '--output', action="store_true", help="If plot option selected, save data output of histogram and timeseries "
                                                                    "analysis in "
                                                                    + directories.ANALYSIS + " as a .dat file.")
    parser.add_argument('-cv', '--covary', action="store_true", help="Analysis on how the variables given in -v "
                                                                     "vary with each other.")
    parser.add_argument('-e', '--ens', nargs=1, type=int,
                        metavar="number_of_ensembles", help="<Required> The number of ensembles of the data. "
                                                            "If not set, the default value = 1", required=True)
    parser.add_argument('-ht', '--hist', nargs='?', const='fd', default='fd',
                        metavar="number_of_bins_in_histogram", help=" Options for bin size selection. If not set, the "
                                                                    "default value = fd (Freedman "
                                                                    "Diaconis Estimator). The list of the potential "
    "options are listed in: \n"
    "https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram_bin_edges.html#numpy.histogram_bin_edges")
    parser.add_argument('-se', '--save_extract', action="store_true", help="Save extracted (iris.cube) data in pkl file.")
    parser.add_argument('-u', '--user', nargs=2, metavar=('file_name', 'function_name'),
                        help="""Use function written by the user and stored in user_function folder for analysis. 
                        file_name : name of file that contains function in user_function folder
                        function_name : name of function to call 
                        Note: user functions are expected to only take in a cube as an argument. An example of a function 
                        can be found in user_function/example_function.py
                        """)

    # Log output
    old_stdout = sys.stdout
    log_file = open("message.log", "w")
    sys.stdout = log_file

    # Initialise the variables
    algae_type, varbs, start, end, ens, monthly, lat, lon, grid, sample, mask, output, covary, hist, plot, \
        lon_centre, save_ext, func = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
    argv = None
    loaded_data = None
    saved, ens_files, abs_files, full_saved = None, None, None, None
    args_dict = {}

    # If no arguments are given, use input file
    if len(sys.argv) == 1:
        algae_type, start, varbs, ens, end, plot, monthly, grid, sample, mask, output, covary, hist, lon_centre, save_ext, func = file_entry()
    elif len(sys.argv) == 2 and (sys.argv[1] == '-ex' or sys.argv[1] == '--example'):
        algae_type, start, varbs, ens, end, plot, monthly, grid, sample, mask, output, covary, hist, lon_centre, save_ext, func = file_entry(example=True)
    elif len(sys.argv) == 2 and sys.argv[1][-3:] == 'pkl':  # Get pickle file to open
        loaded_data = sys.argv[1]
        # Check that it is a pickle file
        if loaded_data is None or loaded_data[-3:] != 'pkl':
            print("Error in function user_entry : Pickle file must be used.")
            sys.exit()
    else:
        # Arguments
        args = parser.parse_args()

        # Make sure that if save output of graphs is selected, we have also selected plotting
        if args.output and (args.plot is None):
            parser.error("--output requires --plot.")

        algae_type = args.prefix
        start = args.start_date
        varbs = args.vars
        ens = args.ens[0]
        end = args.end_date
        plot = args.plot
        monthly = args.monthly
        grid = args.grid
        sample = args.sample
        mask = args.mask
        output = args.output
        covary = args.covary
        hist = args.hist
        lon_centre = args.lon_centre
        save_ext = args.save_extract
        func = args.user

    # If not loading data from pickle file, then get from command line
    if loaded_data is None:
        # Get command line arguments
        argv = 'python main.py ' + algae_type + ' ' + str(start)
        if end:
            argv = argv + ' ' + end
        av = ' '.join(varbs)
        argv = argv + ' -v ' + av + ' -e ' + str(ens)

        # Get split start date
        day_s, mon_s, yr_s = get_date(start)
        if not end:  # If end date not given, use the end of start year
            if StartBools.just_start_year:
                end = str(yr_s)
            elif StartBools.just_start_year_month:
                end = str(yr_s) + "-" + str(mon_s)

        # Get split end date
        day_e, mon_e, yr_e = get_date(end, start=False)

        # Print user input
        print("Arguments:")
        print("- algae type: ", algae_type)
        print("- variables: ", varbs)
        print("- start date: " + str(yr_s) + "-" + str(mon_s) + "-" + str(day_s))
        print("- end date: " + str(yr_e) + "-" + str(mon_e) + "-" + str(day_e))

        # Check that dates are in valid order
        is_valid = check_valid_order([day_s, mon_s, yr_s], [day_e, mon_e, yr_e])
        if not is_valid:
            print("Error: Invalid start and end date")
            print("  - The end date is earlier than the start date")
            sys.exit()
        print("Number of ensembles:", ens)
        if plot:
            print("Plotting option selected.")
            argv = argv + ' -p' + str(plot[0])
        if monthly:
            print("Monthly date expected.")
            argv = argv + ' -m'

        if grid:
            lat, lon = grid[0], grid[1]
            print("Grid point option selected.")
            argv = argv + ' -g ' + str(grid[0]) + ' ' + str(grid[1])
        if sample:
            lat, lon = sample[0], sample[1]
            print("Sample point option selected.")
            argv = argv + ' -s ' + str(sample[0]) + ' ' + str(sample[1])

        if mask:
            if isinstance(mask, list):
                mask = mask[0]
            print("Masking grid option selected.")
            argv = argv + ' -mk ' + mask
        if output:
            print("Save analysis data output selected.")
            argv = argv + ' -o'
        if covary:
            print("Co-varying option selected.")
            argv = argv + ' -cv'

        if not hist:
            hist = 'fd'
        elif hist:
            argv = argv + ' -h ' + hist

        print("Histogram bin selection option:", hist)

        if func:
            print("User function given: " + str(func[0]) + ", " + str(func[1]))
            argv = argv + ' -u ' + func[0] + ' ' + func[1]

        if lon_centre:
            lon_centre = lon_centre[0]
            print("Longitude centering option selected.")
            argv = argv + ' -lc ' + str(lon_centre)
        elif not lon_centre:
            lon_centre = None

        # Call functions to perform analysis
        start = [day_s, mon_s, yr_s]
        end = [day_e, mon_e, yr_e]

        # Extract data from files
        saved, ens_files, abs_files, full_saved = extract_data(algae_type, varbs, start, end, ens,
                                                monthly=monthly, lat=lat, lon=lon, grid=grid, lon_centre=lon_centre,
                                                               maskfile=mask)

        # Put all values in dictionary
        args_dict['algae_type'] = algae_type
        args_dict['varbs'] = varbs
        args_dict['start'] = start
        args_dict['end'] = end
        args_dict['ens'] = ens
        args_dict['monthly'] = monthly
        args_dict['lat'] = lat
        args_dict['lon'] = lon
        args_dict['grid'] = grid
        args_dict['lon_centre'] = lon_centre
        args_dict['save_out'] = output
        args_dict['hist'] = hist
        args_dict['plot'] = plot
        args_dict['argv'] = argv
        args_dict['mask'] = mask
        args_dict['func'] = func

        # Save data to pickle file
        if save_ext:
            # Add to arguments
            argv = argv + ' -se'
            args_dict['argv'] = argv
            # Save data to file
            save_extract_data_to_file(saved, full_saved, ens_files, abs_files, args_dict)

    else:
        saved, ens_files, abs_files, args_dict, full_saved = load_extract_data_from_file(loaded_data)

    # COMPUTE ANALYSIS
    # user analysis
    func, user_ens_stats, ens_stats, func_name, analysis_str = None, None, None, None, None
    if args_dict['func']:
        file_name, func_name = func[0], func[1]
        user_ens_stats = compute_user_analysis(saved, file_name, func_name)
    else:
        ens_stats, analysis_str = compute_stats_analysis(saved, analysis='mean')

    # PLOTTING
    plot = args_dict['plot']
    if plot is not None:
        plot_ens_num = int(plot[0])

        # Only plot map of analysis if using analysis: mean, median, std or rms and NOT grid/sample point
        if args_dict['lat'] is None:
            plot_map(ens_stats, args_dict['varbs'], save_out=args_dict['save_out'], ens_num=plot_ens_num, analysis_str=analysis_str)

        # Plot histogram
        create_histogram(saved, args_dict['start'], args_dict['end'], args_dict['varbs'], sel=args_dict['hist'], save_out=args_dict['save_out'], ens_num=plot_ens_num)
        # Plot time series and boxplot
        if func is not None:
            create_timeseries(user_ens_stats, args_dict['start'], args_dict['end'], args_dict['varbs'], save_out=args_dict['save_out'], ens_num=plot_ens_num, func_name=func_name)
        else:
            create_timeseries(saved, args_dict['start'], args_dict['end'], args_dict['varbs'], save_out=args_dict['save_out'], ens_num=plot_ens_num, func_name=func_name)

    # WRITE ANALYSIS TO NETCDF FILE
    if func:
        write_user_analysis_to_netcdf_file(ens_files, abs_files, user_ens_stats, func_name, args_dict['varbs'], args_dict['start'], args_dict['end'], args_dict['argv'], test=True)
    else:
        write_means_to_netcdf_file(ens_files, abs_files, ens_stats, analysis_str, args_dict['varbs'], args_dict['start'], args_dict['end'], args_dict['argv'], test=True)

    # End logging
    sys.stdout = old_stdout
    log_file.close()

    # Show graphs
    plt.show()

    # compute_enso_indices()


