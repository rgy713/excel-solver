import sys
import threading

from flask import Flask, request, jsonify
import pulp
import pandas as pd
from PySide2 import QtWidgets

from ui_mainwindow import Ui_MainWindow

app = Flask(__name__)

ABC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
COLS = [ f'{i}' for i in ABC]
for i in range(3):
    COLS += [ f'{ABC[i]}{j}' for j in ABC]

COLS = COLS[2:98]

V_COUNT = 96
E_COUNT = 101

# Upload API
@app.route('/lp-solve', methods=['POST'])
def lp_solve():
    data = request.get_json()
    if data is None:
        return jsonify(
            status="error",
            message="Please set Content-Type='application/json' in headers"
        )
    if type(data) is not dict:
        return jsonify(
            status="error",
            message="Please input json data"
        )

    if len(data) is not 104:
        return jsonify(
            status="error",
            message="Please input correct data (must have keys '12'~'112','6','161','CX')"
        )

    try:
        solution, objective = simplex_lp(data)
    except:
        return jsonify(
                status="error",
                message="Error unknown"
            )

    return jsonify(
                status="success",
                result={
                    "solution": solution,
                    "objective": objective
                }
            )


def get_value(idx, obj):
    if type(obj) is dict or type(obj) is list:
        try:
            if type(obj[idx]) is str and ',' in obj[idx]:
                obj[idx].replace(',', '')
            if obj[idx] == '':
                val = 0
            else:
                val = float(obj[idx])
        except:
            val = 0
        return val
    else:
        return 0

def simplex_lp(input):
    idx = [col for col in range(V_COUNT)]

    d = {
        'col': pd.Series(COLS, index=idx),
    }

    param3 = {}
    for row in range(12, 12 + E_COUNT):
        c_ct = [get_value(col, input[f"{row}"]) if f"{row}" in input.keys() else 0 for col in range(V_COUNT)]

        d[f"{row}"] = pd.Series(c_ct, index=idx)

        param3[f"{row}"] = get_value(row - 12, input["CX"]) if "CX" in input.keys() else 0

    df = pd.DataFrame(d)

    x = pulp.LpVariable.dicts("x", df.index, lowBound=0)
    mod = pulp.LpProblem("diet_cost", pulp.LpMinimize)

    # Objective function
    param1 = [get_value(col, input["6"]) if "6" in input.keys() else 0 for col in range(V_COUNT)]
    param2 = [get_value(col, input["161"]) if "161" in input.keys() else 0 for col in range(V_COUNT)]

    mod += pulp.lpSum([x[i] * param1[i] * param2[i] / 365 for i in df.index])

    print(df)
    print(param1)
    print(param2)
    print(param3)

    # Lower and upper bounds:
    for i in range(12, 36):
        mod += pulp.lpSum([x[j] * df[f"{i}"][j] for j in df.index]) <= param3[f"{i}"]
    for i in range(36, 60):
        mod += pulp.lpSum([x[j] * df[f"{i}"][j] for j in df.index]) >= param3[f"{i}"]
    for i in range(60, 72):
        mod += pulp.lpSum([x[j] * df[f"{i}"][j] / 100 for j in df.index]) <= param3[f"{i}"]
    for i in range(72, 84):
        mod += pulp.lpSum([x[j] * df[f"{i}"][j] / 100 for j in df.index]) >= param3[f"{i}"]
    for i in range(84, 108):
        mod += pulp.lpSum([x[j] * df[f"{i}"][j] for j in df.index]) <= param3[f"{i}"]
    for i in range(108, 112):
        mod += pulp.lpSum([x[j] * df[f"{i}"][j] * param2[j] for j in df.index]) <= param3[f"{i}"]

    mod += pulp.lpSum([x[j] * df[f"112"][j] * param2[j] for j in df.index]) <= param3[f"112"]

    print(df.index)
    # Solve model
    mod.solve()

    # Output solution
    solution = []
    for i in df.index:
        print(i, x[i].value())
        solution.append(x[i].value())

    # ret = []
    # for row in range(12, 12 + E_COUNT):
    #     if row >= 60 and row <= 83:
    #         ret.append(pulp.lpSum([x[i].value() * df[f"{row}"][i]  / 100 for i in range(V_COUNT)]))
    #     elif row >= 108 and row <= 112:
    #         ret.append(pulp.lpSum([x[i].value() * df[f"{row}"][i] * param2[i] for i in range(V_COUNT)]))
    #     else:
    #         ret.append(pulp.lpSum([x[i].value() * df[f"{row}"][i] for i in range(V_COUNT)]))
    #
    # print(ret)

    objective = pulp.value(mod.objective)

    print('Objective', objective)

    return solution, objective

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        t = threading.Thread(name="start_server", target=self.start_server, args=[])
        t.setDaemon(True)
        t.start()

    def start_server(self):
        app.run(host="localhost", port=5000)

if __name__ == "__main__":
    win_app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(win_app.exec_())