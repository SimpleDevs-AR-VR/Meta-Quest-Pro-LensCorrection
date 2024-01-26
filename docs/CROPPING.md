# Meta Quest Pro Lens Correction: Cropping Parameters

Cropping parameters were determined based on the following process:

1. Determine the black padding on the right side of the raw capture, from the edge of the image to the white background seen in a template image rendered to both eyes.
2. Starting from an equivalent leftmost white background point on the left eye capture, subtract the derived padding to find the mirrored "edge" of the leftmost side.
3. Crop the footage such that the extraneous padding to the left is removed.
4. Calculate the window size of each eye by cropping the altered frame half vertically. Both left and right crops should be equivalent in width and height, as a result.

## Calculating Cropping Parameters

This process can be performed for ANY aspect ratio raw footage capture from **scrcpy** and the Meta Quest Pro. This can be tested by running the python script `src/FindCropDimensions.py`, which accepts two arguments:

|Command Flag|Argument Type|Value Type|Description|
|:-|:-|:-|:-|
|`source`|positional|`str`|Indicate the relative filepath to an **image** that must be cropped.|
|`-p`, `--preview`|optional|`bool`|Tell the script if you wish to preview the crop prior to splitting between left and right eye views|

An example command would be:

````bash
python src/FindCropDimensions.py <input_image>.png -p True
````

When inputted properly, this script will save the derived cropping parameters in a new text file, in the same directory as your input image.

## I need an image?

If you do not have an image but rather a video, you can get an aspect ratio-accurate frame from your video using the `src/GetScreenshotFromVideo.py` script, which has 2 required arguments:

|Command Flag|Argument Type|Value Type|Description|
|:-|:-|:-|:-|
|`source`|positonal|`str`|The movie or video file that you want to get a screenshot from|
|`timestamp`|positional|`int`|At what explicit second do you want to get the screenshot from? MUST be in seconds - for example, a timestamp of `00:01:30` must be typed as `90`.|

## Final **ffmpeg** Cropping Command

We must use the **ffmpeg** package for the final cropping. The command and its arguments is as follows:

````bash
ffmpeg -i <INPUT_VIDEO_PATH> -vf "crop=out_x:out_y:x:y" -vsync 2 <OUTPUT_VIDEO_PATH>
````

* `out_w`: The width of the cropped area
* `out_h`: The height of the cropped area
* `x`: The x-coordinate of the topleft corner of the cropped area
* `y`: The y-coordinate of the topleft corner of the cropped area

_**NOTE**: Do NOT forget the `-vsync 2` flag, otherwise your code will take forever._

## `ffmpeg` Cropping Templates

We've derived some parameters for two specific aspect ratio formats offered by **scrcpy**:

|Format flag|Aspect Ratio|Extra Leftside Padding|Eye Cam Width|Left Eye|Right Eye|
|:-|:-|:-|:-|:-|:-|
|`-m1080`|1080 x 568|?|?|`out_x=534`<br>`out_y=568`<br>`x=12`<br>`y=0`|`out_x=534`<br>`out_y=568`<br>`x=546`<br>`y=0`|
|`-m1280`|1280 x 672|16px|632px|`out_x=632`<br>`out_y=672`<br>`x=16`<br>`y=0`|`out_x=632`<br>`out_y=672`<br>`x=648`<br>`y=0`|
