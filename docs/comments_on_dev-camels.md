### Daily plot

* It's interesting that the platform allows to switch the discharge time series from $mm$ to $m³/s$, making use of the time series `discharge_mm` and `discharge_cms`. However, in the current setup, it's not easy to compare precipitation and discharge. The default plot should show both discharge and precipitation in $mm$, so the user can easily compare how feasible are the discharge values by comparing against precipitation. For that reason, the Y axis should be one and the discharge line plot overlays the precipitation bar plot. If the user selects the units $m³/s, I would recommend a second Y axis, but do not invert the precipitation axes.
* The logarithmic and square root transformations should apply to both precipitation and discharge.
* The horizontal line of mean discharge is not interesting.


### Annual plot

* I would like to see both discharge (a line plot) and precipitation (a bar plot). The idea is to check wether the annual discharge is realistic in comparison to the precipitation (it should not be higher and should not be excessively low).
* No need to switch it on and off. Always show the annual plot.

### Missing data plot

* Could it only show the missing values? The questionnaire will prompt the user to define the periods with good data. I find it very useful if I can see easily the first/last date of the missing data period. As it is now, it is very hard to identify those dates.
* No need to switch it on and off. Always show the annual plot.
