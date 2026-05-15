from pathlib import Path
p = Path("streamlit_app.py")
t = p.read_text(encoding="utf-8")
t = t.replace('    d = "motion"\n    d = "motion"', '    d = "motion"')
t = t.replace('    d = "motion"\n    d = "div"', '    d = "div"')
# any remaining motion tag typos
tag = "mo" + "tion"
t = t.replace("<" + tag + " ", "<div ")
t = t.replace("<" + tag + ">", "<motion>")
t = t.replace("<" + tag + " class", "<div class")
t = t.replace("</" + tag + ">", "</div>")
p.write_text(t, encoding="utf-8")
print("fixed")
