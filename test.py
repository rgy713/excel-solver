import numpy as np
import pandas as pd
idx = [0, 1, 2]
d = {'channel': pd.Series(['Channel1', 'Channel2', 'Channel3'], index=idx),
     '30-day Cost': pd.Series([1765.21, 2700., 2160.], index=idx),
     'Trials': pd.Series([9865, 1500, 1200], index=idx),
     'Success': pd.Series([812, 900, 333], index=idx),
     'Cost Min': pd.Series([882.61, 1350.00, 1080.00], index=idx),
     'Cost Max': pd.Series([2647.82, 4050.00, 3240.00], index=idx)}
df = pd.DataFrame(d)

import pulp

# Create variables and model
x = pulp.LpVariable.dicts("x", df.index, lowBound=0)
mod = pulp.LpProblem("Budget", pulp.LpMaximize)

# Objective function
objvals = {idx: (1.0/(df['30-day Cost'][idx]/df['Trials'][idx]))*(df['Success'][idx]/float(df['Trials'][idx])) for idx in df.index}
mod += sum([x[idx]*objvals[idx] for idx in df.index])

# Lower and upper bounds:
for idx in df.index:
    mod += x[idx] >= df['Cost Min'][idx]
    mod += x[idx] <= df['Cost Max'][idx]

# Budget sum
mod += sum([x[idx] for idx in df.index]) == 5000.0

# Solve model
mod.solve()

# Output solution
for idx in df.index:
    print(idx, x[idx].value())
# 0 2570.0
# 1 1350.0
# 2 1080.0

print('Objective', pulp.value(mod.objective))
# Objective 1798.70495012