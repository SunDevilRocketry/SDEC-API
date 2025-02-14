# save this as app.py
from flask import Flask

from sdec import sdec

terminalSerObj = sdec.terminalData()

app = Flask(__name__)

@app.route("/comport-l")
def comport():
    userCommand = "comport"
    userArgs = "-l"
    terminalSerObj, ports = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return ports


if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()