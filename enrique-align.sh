poetry run python -m ebl.alignment.align_fragmentarium -l 25000 --minScore 100 --maxLines 10 -o ./align && git add --all && git commit -m "align fragments" && git push
