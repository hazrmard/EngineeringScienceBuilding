Need more varied data in terms of `PerFreqFan[A | B]` to generate controller models.

---

Even when `PerFreqFanA` and `PerFreqFanB` are 1, sometimes `PowFanA` and `PowFanB` are still 0. This makes average fan power plots suspect. In the original excel file, the column formatting  on fan power shows `-` for 0 values. The `-` may indicate that the power measurement is unchanged from last timestamp (anot not necessarily 0). However, there are `-` also for the case when input power and fan speed are `-`/0 which should imply that `-` in power column is actually 0. Conflicting interpretations?

*Ans*: Zero values may be due to network traffic/ power fluctuation issues.
*Course of action*: Discard rows with 0 measurements in any power field.

---

What is the cooling mechanism in the cooling tower? Dry/wet/fluid?

---

What is the current control logic?

---

Learn a model from temps/flow rates --> fan speed. Regularization will make the controller less jagged than before.

---

Relationship b/w fan speed %, temperature, humidity, and fan power?

*Ans*: Almost no correlation