import re, os, sys, errno
from argparse import ArgumentParser


def main():
    args = marshall_arguments()
    in_file_or_dir = args.file

    if is_dir(in_file_or_dir):
        process_directory(in_file_or_dir)
    else:
        in_file = in_file_or_dir
        rules = process_rules_file(in_file)
        do_line_replacements(rules, in_file)


class ccolor:
    END = '\033[0m'
    BOLD = '\033[1m'
    COLOR = '\033[4m'


class cmsg:
    DOTTEDLINE = '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - '


class Replacement(object):
    def __init__(self, replacement):
        self.replacement = replacement
        self.matched = None
        self.replaced = None

    def __call__(self, match):
        self.matched = match.group(0)
        self.replaced = match.expand(self.replacement)
        return self.replaced


def is_valid_file_or_dir(parser, arg):
    if not os.path.exists(arg):
        parser.error("%s does not exist!" % arg)
    else:
        if is_dir(arg):
            return arg
        else:
            return open(arg, 'r')  # return an open file handle


def write_output_file(file_name, result):
    text_file = open(file_name, "w")
    text_file.write(result)
    text_file.close()


def replace_lines(lines_to_match, replacement_lines, targetString):
    regex_to_match = "(\n\s*)"
    replacement_text = "\g<1>"
    regex_group_count = 2

    print cmsg.DOTTEDLINE
    print ccolor.BOLD + "All occurrences of:" + ccolor.END

    for step in lines_to_match:
        regex_to_match = regex_to_match + step + "(\s*\n\s*)"
        print "\t" + step

    print ccolor.BOLD + "have been replaced with:" + ccolor.END

    for step in replacement_lines:
        replacement_text = replacement_text + step + "\g<" + str(regex_group_count) + ">"
        print "\t" + step
        regex_group_count += 1

    processed_text = re.subn(regex_to_match, replacement_text, targetString, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)

    print ccolor.BOLD + (str(processed_text[1]) + " replacements performed in this stage") + ccolor.END
    print cmsg.DOTTEDLINE

    return processed_text[0]


def marshall_arguments():
    global parser
    parser = ArgumentParser(description="The Axiomatic Text Recomposer v0.0.1")
    parser.add_argument(dest="file",
                        help="name of the *.feature file (or directory) to process.  \n(NB - Directory MUST contain a *.rules file.)",
                        metavar="FEATURE_FILE",
                        type=lambda x: is_valid_file_or_dir(parser, x))

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-o', '--output',
                       help='specify output file.  Default: modify input file(s) in place')

    return parser.parse_args()


def get_extension(file):
    if not type(file) is str:
        file = file.name

    return os.path.splitext(file)[1]


def is_dir(arg):
    if not type(arg) is str:
        arg = arg.name

    return os.path.isdir(arg)


def process_rules_file(ff):
    if is_dir(ff):
        directory_containing_ff = ff
    else:
        directory_containing_ff = os.path.dirname(os.path.realpath(ff.name))

    rules_file = ""
    missing_rules_file = True

    for root, dirs, files in os.walk(directory_containing_ff):
        for file in files:
            if file.endswith(".rules"):
                print("Using Rules file: " + os.path.join(root, file))
                missing_rules_file = False
                rules_file = open(os.path.join(root, file))

    if missing_rules_file:
        print "Error: No rules list was found.\n"
        parser.print_help()
        sys.exit(errno.ENOENT)

    rules_list = []
    add = []
    sub = []
    for line in rules_file:
        if line.lstrip().startswith("-"):
            add.append(line.lstrip().lstrip("-").lstrip().strip())
        elif line.lstrip().startswith("+"):
            sub.append(line.lstrip().lstrip("+").lstrip().strip())
        else:
            # only add the rules to the rules list if there is a rule to add (catches multiple empty lines)
            if add:
                rules_list.append([add, sub])
                add = []
                sub = []
    if add:
        rules_list.append([add, sub])

    return rules_list


def do_line_replacements(master_rule_list, ff):
    ff_name = ff.name
    feature_text = ff.read()
    for lrr in master_rule_list:
        old_steps = lrr[0]
        new_steps = lrr[1]
        feature_text = replace_lines(old_steps, new_steps, feature_text)
    write_output_file(ff_name, feature_text)


def process_directory(dir):
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(".feature"):
                in_file = dir
                rules = process_rules_file(in_file)
                do_line_replacements(rules, in_file)


main()
