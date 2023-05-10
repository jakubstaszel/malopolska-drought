import sys
from streamlit.web import cli

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "./src/webapp/Home.py"]
    sys.exit(cli.main())
