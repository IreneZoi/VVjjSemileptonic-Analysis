#!/bin/bash

usage() {
  echo "Usage: $0 [ -f FILE ] [ -o OUTPUT ] [ -t TYPE ]" 1>&2
  echo ""
  echo "   -f Input ipynb file (default: plots_variables.ipynb)"
  echo "   -o Output filename (default extracted from input)"
  echo "   -t Output type pdf or html (default: pdf)"
}

exit_abnormal() {
  usage
  exit 1
}

while getopts ":f:o:t:" opt; do
  case "${opt}" in
    f) FILE=${OPTARG};;
    o) OUTPUT=${OPTARG};;
    t) TYPE+=("${OPTARG}");;
    :)
      echo "Error: -${OPTARG} requires an argument."
      exit_abnormal
      ;;
    *)
      exit_abnormal
      ;;
  esac
done

if [ "$FILE" == "" ]; then
    input=plots_variables.ipynb
else
    input=$FILE
fi

if [ "$OUTPUT" == "" ]; then
    output=$(grep -oh "hist_filename = .*root" ${input} | cut -d '"' -f 2 | cut -d '.' -f 1)
else
    output=$OUTPUT
fi
echo $output

if [ "$TYPE" == "" ]; then
    TYPE=("pdf")
fi

for type in ${TYPE[*]}; do
    if [ "$type" == "pdf" ]; then
      python -m jupyter nbconvert --to pdf ${input} --output ${output}.pdf  --PDFExporter.exclude_input=True
    fi

    if [ "$type" == "html" ]; then
        python -m jupyter nbconvert --to html ${input} --output ${output}.html  --TemplateExporter.exclude_input=True
    fi
done
exit
