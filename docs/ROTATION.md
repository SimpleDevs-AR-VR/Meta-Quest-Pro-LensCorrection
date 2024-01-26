# # Meta Quest Pro Lens Correction: Rotation Parameters

[After cropping](./CROPPING.md), you will perhaps want to rotate each eye such that their horizontal plane is truly horizontal. To do so, one simply has to perform some visual observation to estimate what that rotation amount is for each eye.

Visual analysis shows that each eye is rotated by 21 degrees; the left eye is 21 degrees counter-clockwise, while the right eye is 21 degrees clockwise. To rotate each eye footage back so that the rotation is set to 0, you can use **ffmpeg**. The required command is provided below:

````bash
ffmpeg -i <INPUT_VIDEO_PATH> -vf "rotate=<DEGREES>*(PI/180)" <OUTPUT_VIDEO_PATH>
````

This command will work regardless of the aspect ratio of the original video. The parameters are as such:
|Eye|Degree Amount|Command|
|:-|:-|:-|
|Left|`21`|`rotate=21*(PI/180)`|
|Right|`-21`|`rotate=-21*(PI/180)`|