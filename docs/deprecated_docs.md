# Meta Quest Pro Lens Correction: Deprecated Documentation

## Legacy Correction Parameters

The two parameters `k1` and `k2` were determined based on visual observation and comparison of results derived using an older version of `EstimateDistortion.py`. The older, deprecated code is still available in this python script, but this script is deprecated.

If you want to use it, it's still available. But note that it'll perhaps run for a long time as it tries to estimate `k2` and `k1`. To make it run, you'll also need a template image - the original image rendered to the user in VR that is flat and straight. The script will attempt to use different parameters to estimate what `k2` and `k1` are, by determining which pair will lead to the closest number of lines as the number estimated from the original template image. The template image in question is provided in `template/DistorationTestGrid2.png`. THe optimal results were found below:

* `k2`: `0.3`
* `k1`: `-0.55`

## Notes on Executable Python Scripts

This repository comes with two script files:

* `EstimateDistortion.py`
* `GetScreenshotFromVideo.py`

The 2nd file is purely for debugging. The key star of the show is the 1st file, `EstimateDistortion.py`. This script, when called, produces multiple possible parameters for `k1` and `k2` and visualizes the results for us.

To call this script, simply execute:

````bash
python EstimateDistortion.py
````

**Please be aware of the following**:

* You must have an empty `inputs`, `processing`, and `output` directories located in the same local directory as the script. The script will not work without these folders present.
* The script, when called, produces multiple possible combinations of `k1` and `k2`. It's YOUR job to look through these and determine what's the best possible combination.
* The total runtime is intense. Make sure you have something you can do in the meantime. Total runtime can range between 10 to 20 minutes.
* This step of the process can be performed in post, meaning you don't need to run this script on the Rasberry Pi 4. You can easily just use the Rasberry Pi 4 for the video recording, then run this part of the pipeline on your more-powerful PC setup.