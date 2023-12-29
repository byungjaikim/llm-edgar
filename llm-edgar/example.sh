#!/bin/bash

# Loop through daybefore values
for ((daysago=0; daysago>=0; daysago--)); do
  echo "Running with daysago=$daysago"
  python run.py --do_llm_tasks --daysago $daysago
done
