## Image to AP Utility

Install Dependencies:

```
pip install PIL numpy matplotlib gdspy
```

Usage: 

```
python3 AL_AP_artwork_stripes.py
```

* Enter image prefix (e.g. enter AMK for AMK.png)
* Enter target width in µm
* Import AL_AP_artwork_output.gds to your library, and instantiate AL_AP_artwork in your top layout

Right now the only "modulation scheme" supported is "stripes". Due to the DRC rule limitation you can't have very high pixel density on the AP layer. Consider M8~9 if necessary.