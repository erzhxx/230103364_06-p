# Task 07 — Maximum tolerable serial fraction

Given `P=8192` and `S(P)>=7500`, Gustafson gives
`8192-alpha(8192-1)>=7500`.
Thus `alpha*8191 <= 692`, and
`alpha_max = 692/8191 = 0.084482359...`.
Therefore the maximum allowable serial fraction is approximately **8.4482%**. At equality the scaled speedup is exactly 7,500; any larger alpha violates the requirement.
