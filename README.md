This application was written because the existing camera classification tools available were inadequate.

It is written in open source tools and uses open data. It is based on QGIS for ease of development.
QGIS already has good prototyping tools as well as having python Qt5 GUI widgets for improved interfaces.
The intention is to store the source code on GitHub and submit it to be ratified as an official QGIS plugin.
But since then I have discovered Wildlife Insights and CameraTrap DP schema. So my app will be upgraded to be compatible with the CameraTrap DP schema.
It seems that to process videos we have to split them into frames at some interval, perhaps 1 second using ffmpeg first.
Ha, with Open-CV installed I can process videos without splitting, but sequences from videos are probably a better way to go.
Without Open-CV we can fall back on the default video player on the laptop without first frame previews.

Copyright Creative Commons 4.0 New Zealand

The latest plugin is now called CoraxClassifier.zip. This includes the help, image loader and the plugin for QGIS.

Kim Ollivier
kimollivier1@gmail.com
