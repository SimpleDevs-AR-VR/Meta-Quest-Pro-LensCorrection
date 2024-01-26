# Meta Quest Pro Lens Correction: Lens Correction Parameters

The algorithm for lens correction is provided by **ffmpeg** and corrects for radial distortion caused by lenses ([src](http://underpop.online.fr/f/ffmpeg/help/lenscorrection.htm.gz)). The same filter is apparently applied in tools like Krita and Digikam. 

$$
r_{src} = r_{tgt}\left( 1 + k_1\left( \frac{r_{tgt}}{r_0} \right)^2 + k_2 \left( \frac{r_{tgt}}{r_0} \right)^4 \right)
$$

where:

* $r_{src}$ = the distance to the focal point in the **target** image
* $r_{tgt}$ = distance to focal point in the **source** image
* $r_0$ = half of the image diagonal
* $k_1, k_2$ = hyperparameters for correction

This is implemented through `ffmpeg`'s `lenscorrection` filter, which accepts a `cx`, `cy`, `k1`, and `k2` as hyperparameters.

````bash
ffmpeg -i <INPUT_VIDEO_PATH> -vf "lenscorrection=cx=<CX>:cy=<CY>:k1=<K1>:k2=<K2>" -vsync 2 <OUTPUT_VIDEO_PATH>
````

* `CX` and `CY`: the focal point of the image
* `K1` and `K2`: The hyperparameters for correction.

## Estimating Parameters

Estimations for `cx`, `cy`, `k2`, and `k1` were found using `src/VisualizeCorrection.py`. If you are wondering why `cx` and `cy` also have to be estimated, it's because it's kind of stupidly hard to actually determine what the focal point would be in this situation. We could perhaps use a template image that has a center image clearly defined? But this is not so easy in practice.

To get started, you can simply call this python code and provide a template image (either the left or right eye) to start correcting. An interface will pop up to let you control each of these four parameters. You can thus use visual observation to estimate which combination of parameters would work best.

## Estimated Parameters

The findings from this visualization are written below for the left and right eye cam images.

|Eye Side|cx|cy|k2|k1|Command|
|:-|:-:|:-:|:-:|:-:|:-|
|Left|0.57|0.51|0.2|-0.48|`lenscorrection=cx=0.57:cy=0.51:k1=-0.48:k2=0.2`|
|Right|0.43|0.51|0.2|-0.48|`lenscorrection=cx=0.43:cy=0.51:k1=-0.48:k2=0.2`|

**NOTE:** the parameters `cy`, `k2`, and `k1` are all the same. it's only `cx` that changes. This makes sense, as the only parameter that's likely to change is the x-coordinate considering that the left and right images are similar otherwise.