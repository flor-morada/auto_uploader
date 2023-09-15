# auto_uploader and grade_shorts.py

Credit goes to Bennett Brixen for creating the AUP format and inspiring this code.
Implementation by Jordan Rodriguez.

## Purpose
Autouploader (AUP) files are a way to specify short problem rules for CSc120.

With AUP, you can ban or require certain syntax nodes for certain problems,
or ban/require certain function/method calls.

Based on these specified restrictions, grade_shorts.py outputs a pdf template,
and a full pdf containing all student code, which can be uploaded to GradeScope
for batch grading.


## AUP syntax
See test.aup for an example.

At the top of each file are rules in the global scope, which apply to all problems.

You can define a new problem with `problem [PROBLEMNAME]`. All rules from one 
problem definition to the next will be applied to that problem.

Rules take on the following form:

`ban/require` + `node/method/function` + `Name of the element`

`ban` rules will flag any instance of the function/method/node they encounter 
as a violation. `require` rules specify that a node/function/method must be present. 

The full list of syntax nodes you can use for `node` rules can be found in [the docs](https://docs.python.org/3/library/ast.html).


## Running the code
First, ensure you have the requirements:

`pip3 install -r requirements.txt`

Then run as follows:

`python3 grade_shorts.py [DIRECTORY]`

`grade_shorts.py` takes one command-line argument, a directory. The directory
should contain a CSV file from CloudCoder, an AUP file for the problem, and a
subdirectory with the student code (also from CloudCoder). 

As I organized it (see .gitignore), all specific info goes into the subdirectory
`assignments`. So `grade_shorts` can be called on `assignments/a1`, `assignments/a2`
and so on.

The constant specified near the top of the file, YEARLY_CONFIG, must be a json
filename with "name_map" (example in 2023-24_config.json) and "ignored_ids".
"name_map" contains names for students whose GradeScope and d2l names are out 
of sync for some reason. You will know which to add because GradeScope will fail
to auto-assign their answers. Match netids to preferred names as they appear on
GradeScope to avoid the hassle of manual assignment. "ignore_ids" contains a list
of netids to not include in the output pdf: instructors, TAs, and dropped students.

It will output two pdfs to the directory you specified: the template to make a 
GradeScope assignment, and the full pdf with student code.
