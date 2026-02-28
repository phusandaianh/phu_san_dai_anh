#!/bin/sh
git ls-files uploads/pricing/ | grep 102429 | while read f; do
  git rm --cached --ignore-unmatch "$f"
done
