import re, os, sys, errno
from argparse import ArgumentParser


parser = ArgumentParser


def main():
    args = marshall_arguments()
    path = args.path

    if is_dir(path):
        process_directory(path, ".feature")
    else:
        process_file(path, ".feature")


class ccolor:
    END = '\033[0m'
    BOLD = '\033[1m'
    COLOR = '\033[4m'


class cmsg:
    DOTTEDLINE = '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - '
    DOTTEDLINE_RGX = '- - REGEX RULE  - - - - - - - - - - - - - - - - - - - - - - - - - - '
    DOTTEDLINE_LRR = '- - LINE REPLACEMENT RULE - - - - - - - - - - - - - - - - - - - - - '
    DOTTEDLINE_WRR = '- - WORD REPLACEMENT RULE - - - - - - - - - - - - - - - - - - - - - '
    BLANKLINE = '\n'


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


def replace_lines(lines_to_match, replacement_lines, target_string):
    regex_to_match = "(\n\s*)"
    replacement_text = "\g<1>"
    regex_group_count = 2

    print cmsg.DOTTEDLINE_LRR
    print ccolor.BOLD + "All occurrences of:" + ccolor.END

    for step in lines_to_match:
        regex_to_match += step + "(\s*\n\s*)"
        print "\t" + step

    print ccolor.BOLD + "have been replaced with:" + ccolor.END

    for step in replacement_lines:
        replacement_text += step + "\g<" + str(regex_group_count) + ">"
        print "\t" + step
        regex_group_count += 1

    processed_text = re.subn(regex_to_match, replacement_text, target_string, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)

    print ccolor.BOLD + (str(processed_text[1]) + " replacement(s) performed in this stage") + ccolor.END
    print cmsg.BLANKLINE

    return processed_text[0]


def replace_regex(regex_rules, replacement_string, target_string):
    print cmsg.DOTTEDLINE_RGX
    print ccolor.BOLD + "Each and every match of the pattern:" + ccolor.END
    print "\t" + regex_rules[0].pattern

    print ccolor.BOLD + "has been replaced with:" + ccolor.END
    print "\t" + replacement_string[0]

    processed_text = re.subn(regex_rules[0], replacement_string[0], target_string)

    print ccolor.BOLD + (str(processed_text[1]) + " replacement(s) performed in this stage") + ccolor.END
    print cmsg.BLANKLINE

    return processed_text[0]


def replace_word(words_to_match, replacement_word, target_string):
    print cmsg.DOTTEDLINE_WRR
    print ccolor.BOLD + "Each and every occurrence of:" + ccolor.END
    print "\t" + words_to_match[0].pattern

    print ccolor.BOLD + "has been replaced with:" + ccolor.END
    print "\t" + replacement_word[0]

    processed_text = re.subn(words_to_match[0], replacement_word[0], target_string)

    print ccolor.BOLD + (str(processed_text[1]) + " replacement(s) performed in this stage") + ccolor.END
    print cmsg.BLANKLINE

    return processed_text[0]


def marshall_arguments():
    global parser
    parser = ArgumentParser(description="The Axiomatic Text Recomposer v0.0.1")
    parser.add_argument(dest="path",
                        help="path to file or directory to process.  \n(NB - Directory MUST contain a *.rules file.)",
                        metavar="PATH",
                        type=lambda x: is_valid_file_or_dir(parser, x))

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-o', '--output',
                       help='specify output file.  Default: modify input file(s) in place')

    return parser.parse_args()


def get_extension(fi):
    if not type(fi) is str:
        fi = fi.name

    return os.path.splitext(fi)[1]


def is_dir(arg):
    if not type(arg) is str:
        arg = arg.name

    return os.path.isdir(arg)


def process_rules_file_in_dir_containing(ff):
    if is_dir(ff):
        directory_containing_ff = ff
    else:
        directory_containing_ff = os.path.dirname(os.path.realpath(ff.name))

    rules_file = ""
    missing_rules_file = True

    for root, dirs, files in os.walk(directory_containing_ff):
        for fi in files:
            if fi.endswith(".rules"):
                print("Using Rules file: " + os.path.join(root, fi))
                missing_rules_file = False
                rules_file = open(os.path.join(root, fi))

    if missing_rules_file:
        print "Error: No rules list was found.\n"
        parser.print_help()
        sys.exit(errno.ENOENT)
    previous_rule_type = ""
    rules_list, line_add_rule, line_sub_rule, word_sub_rule, word_add_rule, regx_mat_rule, regx_rpl_rule = [], [], [], [], [], [], []
    # TODO consider a better pattern for this. At minimum, replace "get_rule_type(rule), add_rule(rule_type) and a dictionary
    for rule in rules_file:
        rule_type = get_rule_type(rule)
        rule = clean_rule(rule, rule_type)
        # ignore comments
        if rule_type == "##":
            continue
        # line replacement rules
        elif rule_type == "l-":
            line_add_rule.append(rule)
        elif rule_type == "l+":
            line_sub_rule.append(rule)
        # word replacement rules
        elif rule_type == "w-":
            escaped_string = re.escape(rule)
            word_sub_rule.append(re.compile(escaped_string))
        elif rule_type == "w+":
            escaped_string = re.escape(rule)
            word_add_rule.append(escaped_string)
        # regex rules
        elif rule_type == "r-":
            regx_mat_rule.append(re.compile(rule, flags=re.IGNORECASE))
        elif rule_type == "r+":
            regx_rpl_rule.append(rule)
        elif rule_type == "ri-":
            regx_mat_rule.append(re.compile(rule))
        elif rule_type == "r-\i":
            regx_mat_rule.append(re.compile(rule.rstrip("\i")))
        elif rule_type == "ri+":
            regx_rpl_rule.append(rule)
        # blank lines
        elif rule_type == "blank":
            if previous_rule_type != "blank":
                rules_list.append([line_add_rule, line_sub_rule, word_sub_rule, word_add_rule, regx_mat_rule, regx_rpl_rule])
                line_add_rule, line_sub_rule, word_sub_rule, word_add_rule, regx_mat_rule, regx_rpl_rule = [], [], [], [], [], []
        else:
            # only add the rule to the rules list if there is a rule to add (catches multiple empty lines)
            if len(line_add_rule) > 0 or len(word_add_rule) > 0 or len(regx_mat_rule) > 0:
                rules_list.append([line_add_rule, line_sub_rule, word_sub_rule, word_add_rule, regx_mat_rule, regx_rpl_rule])
                line_add_rule, line_sub_rule, word_sub_rule, word_add_rule, regx_mat_rule, regx_rpl_rule = [], [], [], [], [], []
        previous_rule_type = rule_type

    # add final rule to rule list
    if len(line_add_rule) > 0 or len(word_add_rule) > 0 or len(regx_mat_rule) > 0:
        rules_list.append([line_add_rule, line_sub_rule, word_sub_rule, word_add_rule, regx_mat_rule, regx_rpl_rule])

    return rules_list


def clean_rule(rule, rule_type):
    return rule.lstrip().lstrip("-").lstrip("+").lstrip(rule_type).lstrip().strip()


def get_rule_type(rule):
    rule = rule.lstrip()
    if len(rule) == 0 or rule.isspace():
        rule_type = "blank"
    elif rule[0] == "#":
        rule_type = "##"
    elif rule[0] == "-" or rule[0] == "+":
        rule_type = "l" + rule[0]
    elif len(rule) > 2 and rule[0:3] == "ri-":
        rule_type = "ri-"
    elif len(rule) > 2 and rule[0:3] == "ri+":
        rule_type = "ri+"
    elif len(rule) > 4 and rule[0:2] == "r-" and rule[-2:] == "\i":
        rule_type = "r-\i"
    else:
        if len(rule) < 2:
            rule_type = "??"
        else:
            rule_type = rule[0:2]
    return rule_type


def process_line_replacement_rules(master_rule_list, text):
    num_rules_processed = 0
    for rule in master_rule_list:
        lines_to_delete = rule[0]
        replacement_lines = rule[1]
        if len(lines_to_delete) > 0:
            text = replace_lines(lines_to_delete, replacement_lines, text)
            num_rules_processed += 1
    return text


def process_regex_rules(master_rule_list, text):
    num_rules_processed = 0
    for rule in master_rule_list:
        match_regex = rule[4]
        replacement_string = rule[5]
        if len(match_regex) > 0:
            text = replace_regex(match_regex, replacement_string, text)
            num_rules_processed += 1
    return text


def process_word_replacement_rules(master_rule_list, text):
    num_rules_processed = 0
    for rule in master_rule_list:
        target_word = rule[2]
        replacement_word = rule[3]
        if len(target_word) > 0:
            text = replace_word(target_word, replacement_word, text)
            num_rules_processed += 1
    return text


def process_directory(direc, file_type_to_process):
    for root, dirs, files in os.walk(direc):
        for f in files:
            process_file(open(direc + "/" + f, "r"), file_type_to_process)


def process_file(fi, fi_type):
    if fi.name.endswith(fi_type):
        in_file = fi
        # TODO: The rules file should be processed once for each unique directory, not once per file
        rules = process_rules_file_in_dir_containing(in_file)
        text = in_file.read()
        text = process_regex_rules(rules, text)
        text = process_line_replacement_rules(rules, text)
        text = process_word_replacement_rules(rules, text)
        write_output_file(fi.name, text)


main()
