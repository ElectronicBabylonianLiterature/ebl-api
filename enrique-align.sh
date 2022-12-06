poetry run python -m ebl.alignment.align_fragmentarium -l 1 --minScore 100 --maxLines 1 -o ./test -w20 && git add --all && git commit -m "align fragments" && git push
